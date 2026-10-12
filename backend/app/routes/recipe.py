import logging
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.recipe import RecipeRequest, RecipeResponse
from app.services.recipe_service import RecipeService, get_recipe_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipe", tags=["Recipe Generation"])


@router.post(
    "/generate",
    response_model=RecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate recipe using local Generative AI",
    description="Accepts confirmed ingredients and preferences, prompts local FLAN-T5 model, and returns structured recipe instructions.",
)
async def generate_recipe(
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
