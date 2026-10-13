import logging
import os
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.schemas.recipe import RecipePreferences, RecipeRequest, RecipeResponse
from app.services.recipe_parser import parse_recipe_text
from app.services.recipe_retriever import RecipeRetriever, get_recipe_retriever

logger = logging.getLogger(__name__)

# Pretrained Qwen2.5-3B-Instruct model ID
DEFAULT_GENAI_MODEL = os.getenv("GENAI_MODEL", "Qwen/Qwen2.5-3B-Instruct")


class RecipeService:
    """
    Local Generative AI service for recipe synthesis using pretrained Qwen2.5-3B-Instruct
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

            # Use float32 on CPU, bfloat16/float16 on CUDA
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info(
                f"[RecipeService] Successfully loaded '{self.model_name}' on device '{self.device}'."
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
    ) -> List[Dict[str, str]]:
        """
        Constructs chat messages for Qwen2.5-3B-Instruct.
        Injects ONLY a small, relevant set of candidate recipes (top 2-3) into the prompt.
        """
        ing_list = ", ".join(ingredients)
        extras = preferences.additionalIngredients.strip() if preferences.additionalIngredients else "None"

        # Build concise reference block from retrieved recipes
        ref_text = ""
        for i, cand in enumerate(candidates[:2], 1):
            raw_ings = cand.get("ingredients_raw", "")
            steps = cand.get("instructions", "")
            # Truncate steps to keep prompt compact and fast
            steps_preview = ". ".join([s.strip() for s in steps.split("\n") if len(s.strip()) > 5][:3])
            ref_text += f"\nReference Recipe {i}: {cand.get('name')}\n"
            ref_text += f"- Ingredients: {raw_ings[:180]}\n"
            ref_text += f"- Key Steps: {steps_preview[:250]}\n"

        system_prompt = (
            "You are DishGenie, a master culinary AI chef. Your task is to generate an authentic, "
            "delicious, and practical recipe tailored to the user's pantry ingredients and culinary constraints. "
            "Use the provided reference recipes for cooking technique and spice balance inspiration. "
            "Output the recipe with structured sections: "
            "RECIPE NAME, DESCRIPTION, INGREDIENTS, INSTRUCTIONS, SUBSTITUTIONS, SHOPPING LIST."
        )

        user_prompt = (
            f"Please generate a complete recipe using these detected ingredients: {ing_list}\n"
            f"User Preferences:\n"
            f"- Diet: {preferences.diet}\n"
            f"- Cuisine: {preferences.cuisine}\n"
            f"- Target Cooking Time: {preferences.cookingTime} minutes\n"
            f"- Difficulty: {preferences.difficulty}\n"
            f"- Servings: {preferences.servings}\n"
            f"- Additional Pantry Ingredients: {extras}\n\n"
            f"Retrieved Database Reference Recipes (Inspiration):{ref_text}\n\n"
            "Generate the full step-by-step recipe now:"
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, request: RecipeRequest) -> RecipeResponse:
        """
        Generates a recipe using local database retrieval and Qwen2.5-3B-Instruct inference.
        Parses output into the structured Recipe schema, maintaining the /api/recipe/generate contract.
        """
        if not self.is_available:
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
                    request.ingredients, request.preferences, candidates
                )
                text = self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
                model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

                with torch.no_grad():
                    generated_ids = self.model.generate(
                        **model_inputs,
                        max_new_tokens=450,
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

                if recipe:
                    return RecipeResponse(success=True, recipe=recipe, raw_text=raw_text)
                else:
                    return RecipeResponse(success=True, recipe=None, raw_text=raw_text)

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
