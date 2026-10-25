from typing import List, Optional
from pydantic import BaseModel, Field


class Prediction(BaseModel):
    name: str = Field(..., description="Predicted ingredient or vegetable name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")


class TopPrediction(BaseModel):
    name: str = Field(..., description="Candidate ingredient name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")


class BoundingBox(BaseModel):
    x: int = Field(..., description="X coordinate of top-left corner")
    y: int = Field(..., description="Y coordinate of top-left corner")
    w: int = Field(..., description="Width of bounding box")
    h: int = Field(..., description="Height of bounding box")


class DetectionItem(BaseModel):
    ingredient: str = Field(..., description="Detected ingredient name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    box: BoundingBox = Field(..., description="Bounding box coordinates")
    freshness_score: float = Field(..., ge=0.0, le=1.0, description="Calculated freshness score")
    expiry_days: int = Field(..., ge=1, description="Estimated days until expiration")
    status: str = Field(..., description="Freshness status: Fresh, Medium, or Use First")


class InventoryItemResponse(BaseModel):
    ingredient: str = Field(..., description="Ingredient name")
    count: int = Field(..., ge=1, description="Aggregated count of detected instances")
    min_expiry_days: int = Field(..., ge=1, description="Minimum days remaining before expiration among items")
    status: str = Field(..., description="Freshness state: Fresh, Medium, or Use First")


class VisionResponse(BaseModel):
    prediction: Prediction = Field(..., description="Primary prediction (for backwards compatibility)")
    top_predictions: List[TopPrediction] = Field(default_factory=list, description="Top predicted candidates")
    inventory: List[InventoryItemResponse] = Field(default_factory=list, description="Aggregated inventory with item counts and expiry")
    detections: List[DetectionItem] = Field(default_factory=list, description="Individual bounding box detections")
    annotated_image: Optional[str] = Field(None, description="Base64 encoded JPEG data URL with bounding boxes and labels")
    total_items_detected: int = Field(1, description="Total count of recognized produce items")


class ServiceStatus(BaseModel):
    available: bool = Field(..., description="Availability status of the subsystem")


# Alias for backward compatibility
VisionServiceStatus = ServiceStatus


class ServicesStatus(BaseModel):
    vision: ServiceStatus = Field(..., description="Status of vision subsystem")
    recipe: ServiceStatus = Field(..., description="Status of recipe generation subsystem")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Overall system health status")
    services: ServicesStatus = Field(..., description="Subsystem health statuses")
