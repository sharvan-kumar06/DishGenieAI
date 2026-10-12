from typing import List
from pydantic import BaseModel, Field


class Prediction(BaseModel):
    name: str = Field(..., description="Predicted ingredient or vegetable name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")


class TopPrediction(BaseModel):
    name: str = Field(..., description="Candidate ingredient name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")


class VisionResponse(BaseModel):
    prediction: Prediction = Field(..., description="Primary prediction")
    top_predictions: List[TopPrediction] = Field(..., description="Top 3 predicted candidates")


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
