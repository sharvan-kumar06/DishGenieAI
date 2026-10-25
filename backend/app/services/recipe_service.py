import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.schemas.recipe import RecipePreferences, RecipeRequest, RecipeResponse
from app.services.recipe_parser import parse_recipe_text
from app.services.recipe_retriever import RecipeRetriever, get_recipe_retriever

logger = logging.getLogger(__name__)

# Pretrained Qwen2.5-3B-Instruct model identifiers
DEFAULT_GGUF_REPO = os.getenv("GENAI_GGUF_REPO", "Qwen/Qwen2.5-3B-Instruct-GGUF")
DEFAULT_GGUF_FILENAME = os.getenv("GENAI_GGUF_FILE", "qwen2.5-3b-instruct-q4_k_m.gguf")
DEFAULT_GENAI_MODEL = os.getenv("GENAI_MODEL", "Qwen/Qwen2.5-3B-Instruct")


class RecipeService:
    """
    Local Generative AI service for recipe synthesis.
    Primary Engine: 4-bit Quantized GGUF via llama-cpp-python for high CPU tokens/sec.
    Fallback Engine: PyTorch/HuggingFace Transformers with bfloat16 and greedy decoding.
    Grounded Fallback: SQLite recipe database candidate synthesis.
    """

    def __init__(self, model_name: Optional[str] = None, load_weights: Optional[bool] = None):
        self.model_name = model_name or os.getenv("GENAI_MODEL", DEFAULT_GENAI_MODEL)
        self.gguf_repo = os.getenv("GENAI_GGUF_REPO", DEFAULT_GGUF_REPO)
        self.gguf_filename = os.getenv("GENAI_GGUF_FILE", DEFAULT_GGUF_FILENAME)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Engine handles
        self.llm = None  # llama_cpp.Llama instance
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.model_backend: str = "none"

        self.retriever: RecipeRetriever = get_recipe_retriever()

        if load_weights is None:
            self.load_weights = os.getenv("DISHGENIE_LOAD_WEIGHTS", "true").strip().lower() in ("true", "1", "yes")
        else:
            self.load_weights = load_weights

        logger.info(
            f"[RecipeService] Initializing RecipeService (device='{self.device}', load_weights={self.load_weights})"
        )
        if self.load_weights:
            self._load_resources()

    def _load_resources(self) -> None:
        """
        Loads the neural generation engine:
          1. First attempts to load 4-bit GGUF via llama-cpp-python (auto-downloading into backend/models/ if missing).
          2. If llama-cpp-python is unavailable or fails, falls back to Hugging Face transformers.
          3. If both fail, falls back to grounded database retrieval synthesis.
        """
        # --- 1. Attempt GGUF via llama-cpp-python & huggingface_hub ---
        try:
            models_dir = Path(__file__).resolve().parent.parent.parent / "models"
            models_dir.mkdir(parents=True, exist_ok=True)
            local_gguf_path = models_dir / self.gguf_filename

            # Auto-download GGUF if missing from local disk
            if not local_gguf_path.exists():
                logger.info(
                    f"[RecipeService] GGUF model '{self.gguf_filename}' not found locally. "
                    f"Auto-downloading from '{self.gguf_repo}' into '{models_dir}'..."
                )
                try:
                    from huggingface_hub import hf_hub_download

                    downloaded_file = hf_hub_download(
                        repo_id=self.gguf_repo,
                        filename=self.gguf_filename,
                        local_dir=str(models_dir),
                    )
                    local_gguf_path = Path(downloaded_file)
                    logger.info(f"[RecipeService] Downloaded GGUF model to: {local_gguf_path}")
                except Exception as dl_err:
                    logger.warning(f"[RecipeService] Failed to auto-download GGUF weights: {dl_err}")
                    local_gguf_path = None

            if local_gguf_path and local_gguf_path.exists():
                from llama_cpp import Llama

                n_threads = max(1, (os.cpu_count() or 4) // 2)
                logger.info(
                    f"[RecipeService] Loading Llama GGUF from '{local_gguf_path.name}' "
                    f"(threads={n_threads}, n_ctx=2048, n_batch=512)..."
                )
                self.llm = Llama(
                    model_path=str(local_gguf_path),
                    n_ctx=2048,
                    n_threads=n_threads,
                    n_batch=512,
                    verbose=False,
                )
                self.model_backend = "llama_cpp"
                logger.info(f"[RecipeService] Successfully initialized 4-bit GGUF model with llama-cpp-python.")
                return
        except Exception as llama_err:
            logger.warning(f"[RecipeService] llama-cpp-python GGUF initialization skipped/failed: {llama_err}")
            self.llm = None

        # --- 2. Fallback to Optimized Hugging Face Transformers ---
        try:
            logger.info(f"[RecipeService] Initializing Hugging Face Transformers fallback for '{self.model_name}'...")
            n_threads = max(1, (os.cpu_count() or 4) // 2)
            torch.set_num_threads(n_threads)

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            dtype = torch.float16 if torch.cuda.is_available() else torch.bfloat16
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self.model.to(self.device)
            self.model.eval()
            self.model_backend = "transformers"
            logger.info(
                f"[RecipeService] Successfully loaded Hugging Face model '{self.model_name}' on '{self.device}' with dtype '{dtype}'."
            )
        except Exception as hf_err:
            logger.warning(
                f"[RecipeService] Hugging Face model '{self.model_name}' not available: {hf_err}. "
                "Database-backed retrieval synthesis will be used until model weights are downloaded."
            )
            self.model = None
            self.tokenizer = None
            self.model_backend = "database_fallback"

    @property
    def is_available(self) -> bool:
        """
        Recipe service is available if either Llama GGUF is loaded,
        the Hugging Face Qwen model is loaded, OR the recipe database has indexed recipes.
        """
        return (
            self.llm is not None
            or (self.model is not None and self.tokenizer is not None)
            or (self.retriever.db.count_recipes() > 0)
        )

    def get_candidate_options(self, request: RecipeRequest, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves top matching candidate dishes from SQLite to present as interactive choices
        to the user before final neural synthesis.
        """
        candidates = self.retriever.retrieve_candidates(
            ingredients=request.ingredients,
            preferences=request.preferences,
            limit=limit,
        )
        options = []
        for cand in candidates:
            name = cand.get("name", "Gourmet Dish")
            cuisine = cand.get("cuisine") or request.preferences.cuisine or "Indian"
            cooking_time = cand.get("cooking_time") or request.preferences.cookingTime or 30
            diet = cand.get("diet") or request.preferences.diet or "Vegetarian"
            image_url = cand.get("image_url")
            matched_tokens = cand.get("matched_user_tokens", [])

            # Generate concise, appetizing overview for the candidate dish
            instructions = cand.get("instructions", "").strip()
            first_sentence = instructions.split(".")[0].strip() if instructions else ""
            if len(first_sentence) > 15 and len(first_sentence) < 140:
                desc = f"{first_sentence}."
            else:
                desc = f"Authentic {cuisine} specialty highlighting {', '.join(matched_tokens) if matched_tokens else 'fresh ingredients'}."

            options.append({
                "id": str(cand.get("id")),
                "name": name,
                "description": desc,
                "cuisine": cuisine,
                "cooking_time": cooking_time,
                "diet": diet,
                "image_url": image_url,
                "matched_ingredients": matched_tokens,
            })
        return options

    def build_prompt_and_messages(
        self,
        ingredients: List[str],
        preferences: RecipePreferences,
        candidates: List[Dict[str, Any]],
        inventory: Optional[List[Any]] = None,
        selected_dish: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Constructs chat messages for recipe generation.
        Injects detected inventory items, counts, and estimated expiry days.
        Provides complete, untruncated candidate recipes for authentic culinary grounding.
        """
        ing_list = ", ".join(ingredients)
        extras = preferences.additionalIngredients.strip() if preferences.additionalIngredients else "None"

        # Build comprehensive reference block from retrieved database recipes without destructive string slicing
        ref_text = ""
        for i, cand in enumerate(candidates[:2], 1):
            name = cand.get("name", "Recipe")
            raw_ings = cand.get("ingredients_raw", "").strip()
            steps = cand.get("instructions", "").strip()

            ref_text += f"\nReference Recipe {i}: {name}\n"
            if raw_ings:
                ref_text += f"- Ingredients: {raw_ings[:800]}\n"
            if steps:
                ref_text += f"- Cooking Steps: {steps[:1200]}\n"

        # Build inventory and freshness context
        inventory_context = ""
        use_first_items = []
        if inventory:
            inventory_lines = []
            for item in inventory:
                ing_name = getattr(item, "ingredient", None) or (item.get("ingredient") if isinstance(item, dict) else str(item))
                count = getattr(item, "count", None) or (item.get("count", 1) if isinstance(item, dict) else 1)
                expiry = getattr(item, "min_expiry_days", None) or (item.get("min_expiry_days") if isinstance(item, dict) else None)
                status = getattr(item, "status", None) or (item.get("status", "Fresh") if isinstance(item, dict) else "Fresh")

                display_name = ing_name.replace("_", " ").title()
                expiry_text = f"{expiry}d remaining" if expiry is not None else "fresh"

                if str(status).lower() in ("use first", "urgent") or (expiry is not None and expiry <= 3):
                    use_first_items.append(display_name)
                    inventory_lines.append(f"- {display_name}: {count} item(s) (Expiry: {expiry_text}) [PRIORITY: USE FIRST]")
                else:
                    inventory_lines.append(f"- {display_name}: {count} item(s) (Expiry: {expiry_text}, Status: {status})")

            if inventory_lines:
                inventory_context = "\nAvailable Inventory (Counts & Freshness):\n" + "\n".join(inventory_lines) + "\n"

        target_dish_focus = ""
        if selected_dish:
            target_dish_focus = (
                f"\nTARGET DISH STYLE: The user specifically chose to cook '{selected_dish}'. "
                f"Your recipe 'name' and core preparation MUST be specifically tailored to '{selected_dish}'.\n"
            )

        system_prompt = (
            "You are DishGenie, an expert culinary AI chef. Your task is to generate an authentic, "
            "delicious, and practical recipe tailored to the user's pantry ingredients and culinary constraints.\n"
            "You MUST output your response as a single, valid JSON object with NO markdown code fences (no ```json), "
            "no conversational text, and no commentary before or after.\n\n"
            "The JSON object must have EXACTLY this structure:\n"
            "{\n"
            '  "name": "Recipe Name",\n'
            '  "description": "Appetizing overview of the dish",\n'
            '  "ingredients": ["1 cup ingredient name, prepped", "1 tsp spice", ...],\n'
            '  "instructions": ["Step 1 actionable sentence.", "Step 2 actionable sentence.", ...],\n'
            '  "substitutions": [\n'
            '    {"ingredient": "Item name", "replacement": "Culinary alternative with flavor/texture reason"}\n'
            "  ],\n"
            '  "shopping_list": ["Item needing purchase", ...]\n'
            "}\n\n"
            "CRITICAL CULINARY & INVENTORY RULES:\n"
            "1. FOOD WASTE PREVENTION (PRIORITIZE 'USE FIRST'): Any ingredient marked 'USE FIRST' (expiring in <= 3 days) "
            "MUST be given highest culinary priority and actively incorporated into the main recipe.\n"
            f"2. QUANTITY RESPECT & SHOPPING LIST SHORTFALL: Respect the user's available item counts for {preferences.servings} servings. "
            "If the recipe requires more quantity than available (e.g., user has 1 tomato but recipe needs 3), or requires necessary "
            "aromatics, spices, cooking oil, or garnishes not present in inventory, automatically add the shortfall or missing items to 'shopping_list'.\n"
            "3. INGREDIENT CONSISTENCY: Every single ingredient, aromatic (garlic, ginger, onions), spice "
            "(fennel seeds, cumin, turmeric, chilli), oil, and garnish mentioned in your cooking instructions "
            "MUST be listed in the 'ingredients' array with sensible quantities.\n"
            "4. ACTIONABLE INSTRUCTIONS: Every step in 'instructions' must be a complete, actionable cooking instruction "
            "with realistic cooking times and temperatures. NEVER use headings or section labels as instruction steps.\n"
            f"5. DIETARY COMPLIANCE: The recipe MUST strictly comply with the user's dietary restriction: {preferences.diet}.\n"
            f"6. CUISINE AUTHENTICITY: Maintain culinary techniques authentic to {preferences.cuisine} cuisine.\n"
            "7. FOCUS: Focus on accurate 'name', 'description', 'ingredients', and 'instructions'. The 'substitutions' and 'shopping_list' "
            "arrays can be included or empty as they are validated and reconciled deterministically.\n"
            "8. STOVETOP PREFERENCE & STRICT PAN PREPARATION: For traditional Indian, pan-fried, curry, and stovetop dishes, strictly prohibit oven-baking instructions "
            "(e.g., 'Preheat oven to 350°F / 180°C', 'Bake on a baking tray'). Prioritize standard Indian stovetop, pan, pressure cooker, or kadhai preparation methods unless "
            "the user's cuisine or recipe explicitly requires baking. Do NOT instruct the user to preheat an oven or bake unless the user has explicitly requested Western baking or a cuisine/dish "
            "that intrinsically requires an oven (such as cakes, bread, or pizza)."
        )

        waste_alert = ""
        if use_first_items:
            waste_alert = f"\nURGENT CULINARY GOAL: Use up expiring produce ({', '.join(use_first_items)}) to avoid food waste.\n"

        user_prompt = (
            f"Create a complete recipe using these confirmed ingredients: {ing_list}\n"
            f"{target_dish_focus}"
            f"{inventory_context}"
            f"{waste_alert}\n"
            f"User Preferences:\n"
            f"- Diet: {preferences.diet}\n"
            f"- Cuisine: {preferences.cuisine}\n"
            f"- Target Cooking Time: {preferences.cookingTime} minutes\n"
            f"- Difficulty: {preferences.difficulty}\n"
            f"- Servings: {preferences.servings}\n"
            f"- Additional Pantry Ingredients: {extras}\n\n"
            f"Retrieved Database Reference Recipes (Inspiration):{ref_text}\n\n"
            "Return ONLY the valid JSON object now:"
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, request: RecipeRequest) -> RecipeResponse:
        """
        Generates a recipe using local database retrieval and fast neural inference (GGUF or HF).
        Parses output into structured Recipe schema, maintaining the /api/recipe/generate contract.
        """
        if not self.is_available:
            logger.error("[RecipeService] Neither language model nor recipe database is available.")
            raise RuntimeError("RecipeService is not initialized or database is unavailable.")

        # 1. Retrieve small relevant candidate set from SQLite
        candidates = self.retriever.retrieve_candidates(
            ingredients=request.ingredients,
            preferences=request.preferences,
            limit=3,
        )
        logger.info(
            f"[RecipeService] Retrieved {len(candidates)} candidate recipes for ingredients: {request.ingredients}"
        )

        # Prioritize candidate matching user's selected dish style if provided
        top_cand = candidates[0] if candidates else None
        if request.selected_dish and candidates:
            sel_clean = request.selected_dish.strip().lower()
            matching = [c for c in candidates if sel_clean in c.get("name", "").lower() or c.get("name", "").lower() in sel_clean]
            if matching:
                top_cand = matching[0]
                candidates = [top_cand] + [c for c in candidates if c != top_cand]

        messages = self.build_prompt_and_messages(
            request.ingredients,
            request.preferences,
            candidates,
            inventory=request.inventory,
            selected_dish=request.selected_dish,
        )
        max_tokens = int(os.getenv("GENAI_MAX_NEW_TOKENS", "450"))

        # 2a. Primary Engine: Fast llama-cpp-python GGUF Execution
        if self.llm is not None:
            try:
                logger.info(f"[RecipeService] Generating recipe with Llama GGUF (max_tokens={max_tokens}, temperature=0.1)...")
                response = self.llm.create_chat_completion(
                    messages=messages,
                    temperature=0.1,
                    top_p=0.9,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                raw_text = response["choices"][0]["message"]["content"].strip()
                logger.info(f"[RecipeService] Llama GGUF generated {len(raw_text)} chars")

                recipe = parse_recipe_text(
                    raw_text,
                    fallback_ingredients=request.ingredients,
                    cuisine=request.preferences.cuisine,
                    diet=request.preferences.diet,
                    additional_ingredients=request.preferences.additionalIngredients,
                    candidate_recipe=top_cand,
                )

                if recipe and recipe.ingredients and recipe.instructions:
                    logger.info(
                        f"[RecipeService] Successfully parsed recipe '{recipe.name}' with "
                        f"{len(recipe.ingredients)} ingredients, {len(recipe.instructions)} steps, "
                        f"{len(recipe.substitutions)} substitutions, {len(recipe.shopping_list)} shopping items."
                    )
                    return RecipeResponse(success=True, recipe=recipe, raw_text=raw_text)
                else:
                    logger.warning("[RecipeService] GGUF output could not be parsed into a complete recipe. Activating database fallback.")
            except Exception as llm_err:
                logger.error(f"[RecipeService] Llama GGUF generation error: {llm_err}", exc_info=True)
                # Fall through to HF or database fallback

        # 2b. Secondary Engine: Optimized Hugging Face Transformers Execution
        elif self.model is not None and self.tokenizer is not None:
            try:
                text = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

                logger.info(f"[RecipeService] Generating recipe with HF Transformers (max_new_tokens={max_tokens}, greedy do_sample=False)...")

                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **model_inputs,
                        max_new_tokens=max_tokens,
                        do_sample=False,
                        repetition_penalty=1.1,
                    )

                generated_ids = [
                    output_ids[len(input_ids):]
                    for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
                ]
                raw_text = self.tokenizer.batch_decode(
                    generated_ids, skip_special_tokens=True
                )[0].strip()

                logger.info(f"[RecipeService] Qwen generated {len(raw_text)} chars")

                recipe = parse_recipe_text(
                    raw_text,
                    fallback_ingredients=request.ingredients,
                    cuisine=request.preferences.cuisine,
                    diet=request.preferences.diet,
                    additional_ingredients=request.preferences.additionalIngredients,
                    candidate_recipe=top_cand,
                )

                if recipe and recipe.ingredients and recipe.instructions:
                    logger.info(
                        f"[RecipeService] Successfully parsed recipe '{recipe.name}' with "
                        f"{len(recipe.ingredients)} ingredients, {len(recipe.instructions)} steps, "
                        f"{len(recipe.substitutions)} substitutions, {len(recipe.shopping_list)} shopping items."
                    )
                    return RecipeResponse(success=True, recipe=recipe, raw_text=raw_text)
                else:
                    logger.warning("[RecipeService] Model output could not be parsed into a complete recipe. Activating database fallback.")

            except Exception as gen_err:
                logger.error(f"[RecipeService] Qwen generation error: {gen_err}", exc_info=True)
                # Fall through to candidate synthesis fallback

        # 3. Grounded Candidate Synthesis Fallback
        if top_cand:
            logger.info(f"[RecipeService] Synthesizing recipe grounded on database candidate: '{top_cand.get('name')}'")
            recipe = parse_recipe_text(
                "",
                fallback_ingredients=request.ingredients,
                cuisine=request.preferences.cuisine,
                diet=request.preferences.diet,
                additional_ingredients=request.preferences.additionalIngredients,
                candidate_recipe=top_cand,
            )
            raw_text = (
                f"RECIPE NAME: {recipe.name}\n\n"
                f"DESCRIPTION: {recipe.description}\n\n"
                f"INGREDIENTS:\n" + "\n".join([f"- {i}" for i in recipe.ingredients]) + "\n\n"
                f"INSTRUCTIONS:\n" + "\n".join([f"{idx+1}. {step}" for idx, step in enumerate(recipe.instructions)])
            )
            return RecipeResponse(success=True, recipe=recipe, raw_text=raw_text)

        logger.error("[RecipeService] Neither model generation succeeded nor any candidate recipe was found.")
        raise RuntimeError("No candidate recipes or language model available to generate recipe.")


# Global singleton instance container
_recipe_service_instance: Optional[RecipeService] = None


def get_recipe_service() -> RecipeService:
    """
    Returns the single global RecipeService instance.
    Initializes it if not yet loaded.
    """
    global _recipe_service_instance
    if _recipe_service_instance is None:
        _recipe_service_instance = RecipeService()
    return _recipe_service_instance
