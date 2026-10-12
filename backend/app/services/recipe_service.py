import logging
import os
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.schemas.recipe import RecipePreferences, RecipeRequest, RecipeResponse
from app.services.recipe_parser import parse_recipe_text

logger = logging.getLogger(__name__)

# Configurable model name via environment variable
DEFAULT_GENAI_MODEL = os.getenv("GENAI_MODEL", "google/flan-t5-base")
FALLBACK_GENAI_MODEL = "google/flan-t5-small"


class RecipeService:
    """
    Local Generative AI service for recipe synthesis using Hugging Face FLAN-T5.
    Loads model and tokenizer once into memory at startup.
    Runs locally on CPU or GPU without external APIs.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("GENAI_MODEL", DEFAULT_GENAI_MODEL)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForSeq2SeqLM] = None

        logger.info(
            f"[RecipeService] Initializing with model: '{self.model_name}' on device: '{self.device}'"
        )
        self._load_resources()

    def _load_resources(self) -> None:
        """
        Loads the Hugging Face tokenizer and model once into memory.
        If flan-t5-base fails due to resources, gracefully falls back to flan-t5-small.
        """
        try:
            logger.info(f"[RecipeService] Loading tokenizer and model for '{self.model_name}'...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(
                f"[RecipeService] Successfully loaded '{self.model_name}' on device '{self.device}'."
            )
        except Exception as e:
            logger.warning(
                f"[RecipeService] Failed to load '{self.model_name}': {e}. Attempting fallback to '{FALLBACK_GENAI_MODEL}'..."
            )
            try:
                self.model_name = FALLBACK_GENAI_MODEL
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()
                logger.info(
                    f"[RecipeService] Fallback model '{self.model_name}' loaded successfully on '{self.device}'."
                )
            except Exception as fallback_err:
                logger.critical(
                    f"[RecipeService] Both primary and fallback models failed to load: {fallback_err}",
                    exc_info=True,
                )
                raise RuntimeError(
                    f"Unable to initialize local GenAI model: {fallback_err}"
                ) from fallback_err

    @property
    def is_available(self) -> bool:
        """Checks if model and tokenizer are initialized and ready for generation."""
        return self.model is not None and self.tokenizer is not None

    def build_prompt(
        self, ingredients: List[str], preferences: RecipePreferences
    ) -> str:
        """
        Builds a structured prompt instructing FLAN-T5 to generate a recipe
        incorporating detected ingredients and user preferences.
        """
        ing_list = ", ".join(ingredients)
        extras = preferences.additionalIngredients.strip() if preferences.additionalIngredients else "None"

        prompt = (
            f"Write a full cooking recipe including ingredients, preparation steps, and instructions using {ing_list}.\n"
            f"Diet: {preferences.diet}\n"
            f"Cuisine: {preferences.cuisine}\n"
            f"Cooking time: {preferences.cookingTime} minutes\n"
            f"Difficulty: {preferences.difficulty}\n"
            f"Servings: {preferences.servings}\n"
            f"Additional ingredients: {extras}\n\n"
            f"Recipe:"
        )
        return prompt

    def generate(self, request: RecipeRequest) -> RecipeResponse:
        """
        Generates a recipe using local FLAN-T5 inference and parses it into a structured response.
        If structured parsing fails, returns the raw text gracefully.
        """
        if not self.is_available:
            raise RuntimeError("RecipeService is not initialized or model is unavailable.")

        prompt = self.build_prompt(request.ingredients, request.preferences)
        logger.info(f"[RecipeService] Generating recipe for ingredients: {request.ingredients}")

        try:
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512,
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=350,
                    do_sample=True,
                    temperature=0.75,
                    top_k=50,
                    repetition_penalty=1.1,
                )

            raw_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            logger.info(f"[RecipeService] Generated raw text ({len(raw_text)} chars)")

            # Attempt structured parsing
            recipe = parse_recipe_text(
                raw_text,
                fallback_ingredients=request.ingredients,
                cuisine=request.preferences.cuisine,
                diet=request.preferences.diet,
                additional_ingredients=request.preferences.additionalIngredients,
            )

            if recipe:
                return RecipeResponse(success=True, recipe=recipe, raw_text=raw_text)
            else:
                logger.warning("[RecipeService] Structured parsing failed, returning raw_text fallback.")
                return RecipeResponse(success=True, recipe=None, raw_text=raw_text)

        except Exception as e:
            logger.error(f"[RecipeService] Generation error: {e}", exc_info=True)
            raise RuntimeError(f"Local recipe generation failed: {e}") from e


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
