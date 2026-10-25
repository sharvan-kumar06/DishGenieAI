import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.recipe import (
    CandidateDishOption,
    CandidateOptionsResponse,
    RecipeRequest,
    RecipeResponse,
)
from app.services.recipe_service import RecipeService, get_recipe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipe", tags=["Recipe Generation"])


@router.post(
    "/candidates",
    response_model=CandidateOptionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve top matching dish style options before final recipe generation",
    description="Returns up to 3 candidate recipe styles from the database matching confirmed ingredients and preferences.",
)
def get_recipe_candidates(
    request: RecipeRequest,
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> CandidateOptionsResponse:
    """
    HTTP route handler for candidate options retrieval.
    Allows user to select their desired dish style before neural synthesis.
    """
    if not request.ingredients or len(request.ingredients) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one confirmed ingredient must be provided.",
        )

    try:
        options_data = recipe_service.get_candidate_options(request, limit=3)
        return CandidateOptionsResponse(
            success=True,
            options=[CandidateDishOption(**opt) for opt in options_data],
        )
    except Exception as err:
        logger.error(f"Unexpected error retrieving candidate dish options: {err}", exc_info=True)
        return CandidateOptionsResponse(success=False, options=[])


@router.post(
    "/generate",
    response_model=RecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate recipe using local Generative AI and Recipe Database",
    description="Accepts confirmed ingredients and preferences, retrieves matching database recipes, prompts local Qwen2.5 model, and returns structured recipe instructions.",
)
def generate_recipe(
    request: RecipeRequest,
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> RecipeResponse:
    """
    HTTP route handler for recipe generation.
    Validates input schema and delegates text generation to RecipeService.
    """
    if not request.ingredients or len(request.ingredients) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one confirmed ingredient must be provided.",
        )

    if not recipe_service.is_available:
        logger.error("RecipeService is not available during request execution.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Local Recipe Generation service is currently unavailable. Please check server logs.",
        )

    try:
        response = recipe_service.generate(request)
        return response
    except RuntimeError as run_err:
        logger.error(f"Generation runtime error: {run_err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A runtime error occurred while generating the recipe with the local language model.",
        ) from run_err
    except Exception as err:
        logger.error(f"Unexpected recipe generation error: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during recipe synthesis. Please try again.",
        ) from err
