import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.schemas.vision import VisionResponse
from app.services.vision_service import VisionService, get_vision_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vision", tags=["Vision"])


@router.get(
    "/classes",
    status_code=status.HTTP_200_OK,
    summary="Get all supported ingredient classes",
    description="Returns the full list of 247 ingredient classes supported by the trained CNN.",
)
async def get_supported_classes(
    vision_service: VisionService = Depends(get_vision_service),
):
    """
    Returns the loaded class names list and count for the frontend.
    """
    return {
        "classes": vision_service.class_names,
        "total": len(vision_service.class_names),
    }


@router.post(
    "/predict",
    response_model=VisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict ingredient from food image",
    description="Accepts a multipart image upload, preprocesses it, and runs CNN inference to detect ingredient.",
)
async def predict_ingredient(
    image: UploadFile = File(..., description="Food or vegetable image file to analyze"),
    vision_service: VisionService = Depends(get_vision_service),
) -> VisionResponse:
    """
    HTTP route handler for ingredient detection.
    Performs HTTP payload validation and delegates CNN inference to VisionService.
    """
    # 1. Validate file presence
    if not image or not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image file provided in the request.",
        )

    # 2. Check basic content-type if provided
    if image.content_type and not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{image.content_type}'. Please upload an image file (e.g. JPEG, PNG, WebP).",
        )

    # 3. Read image bytes
    try:
        image_bytes = await image.read()
    except Exception as e:
        logger.error(f"Failed to read image stream: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded image file stream.",
        ) from e

    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty (0 bytes).",
        )

    # 4. Check service availability
    if not vision_service.is_available:
        logger.error("VisionService is not available during request execution.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Computer Vision service is currently unavailable. Please check server logs.",
        )

    # 5. Delegate prediction to VisionService
    try:
        result = vision_service.predict(image_bytes, top_k=3)
        return VisionResponse(**result)
    except ValueError as val_err:
        # Invalid image data / corrupted file
        logger.warning(f"Image validation error: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
    except RuntimeError as run_err:
        logger.error(f"Prediction runtime error: {run_err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the image through the neural network.",
        ) from run_err
    except Exception as err:
        logger.error(f"Unexpected prediction failure: {err}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction. Please try again.",
        ) from err
