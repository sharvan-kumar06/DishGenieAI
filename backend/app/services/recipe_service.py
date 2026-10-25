import logging
import os
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.schemas.recipe import RecipePreferences, RecipeRequest, RecipeResponse
from app.services.recipe_parser import parse_recipe_text
from app.services.recipe_retriever import RecipeRetriever, get_recipe_retriever

logger = logging.getLogger(__name__)

# Pretrained Qwen2.5-1.5B-Instruct model ID (optimized for lightweight local laptop CPU/memory)
DEFAULT_GENAI_MODEL = os.getenv("GENAI_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")


class RecipeService:
    """
    Local Generative AI service for recipe synthesis using pretrained Qwen2.5-1.5B-Instruct
    combined with persistent SQLite recipe database retrieval (RAG).
    Runs purely locally on CPU/CUDA without fine-tuning or external APIs.
    """

    def __init__(self, model_name: Optional[str] = None, load_weights: Optional[bool] = None):
        self.model_name = model_name or os.getenv("GENAI_MODEL", DEFAULT_GENAI_MODEL)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.retriever: RecipeRetriever = get_recipe_retriever()

        if load_weights is None:
            self.load_weights = os.getenv("DISHGENIE_LOAD_WEIGHTS", "true").strip().lower() in ("true", "1", "yes")
        else:
            self.load_weights = load_weights

        logger.info(
            f"[RecipeService] Initializing with model: '{self.model_name}' on device: '{self.device}' (load_weights={self.load_weights})"
        )
        if self.load_weights:
            self._load_resources()

    def _load_resources(self) -> None:
        """
        Loads the Hugging Face tokenizer and Qwen model once into memory.
        If model loading fails (e.g. offline first run or resource limit), logs a warning
        and enables database-augmented synthesis mode.
        """
        try:
            logger.info(f"[RecipeService] Loading tokenizer and model for '{self.model_name}'...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
            )

            # Use float16 on CUDA, bfloat16 on CPU for 50% memory savings and faster compute
            dtype = torch.float16 if torch.cuda.is_available() else torch.bfloat16

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info(
                f"[RecipeService] Successfully loaded '{self.model_name}' on device '{self.device}' with dtype '{dtype}'."
            )
        except Exception as e:
            logger.warning(
                f"[RecipeService] Model '{self.model_name}' not yet loaded locally: {e}. "
                "Database-backed retrieval synthesis will be used until model weights are downloaded."
            )
            self.model = None
            self.tokenizer = None

    @property
    def is_available(self) -> bool:
        """
        Recipe service is available if either Qwen model is loaded OR
        the recipe database has indexed recipes for grounded synthesis.
        """
        return (self.model is not None and self.tokenizer is not None) or (self.retriever.db.count_recipes() > 0)

    def build_prompt_and_messages(
        self,
        ingredients: List[str],
        preferences: RecipePreferences,
        candidates: List[Dict[str, Any]],
        inventory: Optional[List[Any]] = None,
    ) -> List[Dict[str, str]]:
        """
        Constructs chat messages for Qwen2.5-1.5B-Instruct.
        Injects detected inventory items, counts, and estimated expiry days.
        Instructs the model to return strict, valid JSON with all six required recipe sections.
        """
        ing_list = ", ".join(ingredients)
        extras = preferences.additionalIngredients.strip() if preferences.additionalIngredients else "None"

        # Build concise reference block from retrieved recipes
        ref_text = ""
        for i, cand in enumerate(candidates[:2], 1):
            raw_ings = cand.get("ingredients_raw", "")
            steps = cand.get("instructions", "")
            steps_preview = ". ".join([s.strip() for s in steps.split("\n") if len(s.strip()) > 5][:3])
            ref_text += f"\nReference Recipe {i}: {cand.get('name')}\n"
            ref_text += f"- Ingredients: {raw_ings[:180]}\n"
            ref_text += f"- Key Steps: {steps_preview[:250]}\n"

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
            "7. SUBSTITUTIONS: Provide ingredient-specific culinary replacements. Never suggest generic filler or allergens."
        )

        waste_alert = ""
        if use_first_items:
            waste_alert = f"\nURGENT CULINARY GOAL: Use up expiring produce ({', '.join(use_first_items)}) to avoid food waste.\n"

        user_prompt = (
            f"Create a complete recipe using these confirmed ingredients: {ing_list}\n"
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
        Generates a recipe using local database retrieval and Qwen2.5-1.5B-Instruct inference.
        Parses output into the structured Recipe schema, maintaining the /api/recipe/generate contract.
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
        top_cand = candidates[0] if candidates else None

        # 2. If Qwen model is loaded, run local neural text generation
        if self.model is not None and self.tokenizer is not None:
            try:
                messages = self.build_prompt_and_messages(
                    request.ingredients,
                    request.preferences,
                    candidates,
                    inventory=request.inventory,
                )
                text = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

                max_tokens = int(os.getenv("GENAI_MAX_NEW_TOKENS", "850"))
                logger.info(f"[RecipeService] Starting Qwen generation (max_new_tokens={max_tokens})...")

                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **model_inputs,
                        max_new_tokens=max_tokens,
                        temperature=0.7,
                        top_p=0.9,
                        do_sample=True,
                    )

                # Slice prompt output
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
        # Synthesizes recipe directly from best matching database candidate
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
