import logging
import sys
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.routes.recipe import router as recipe_router
from app.routes.vision import router as vision_router
from app.schemas.vision import HealthResponse, ServiceStatus, ServicesStatus
from app.services.recipe_service import RecipeService, get_recipe_service
from app.services.vision_service import VisionService, get_vision_service

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("dishgenie")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler to ensure fail-fast model loading once on startup.
    Loads both VisionService (CNN) and RecipeService (FLAN-T5) into memory once.
    """
    logger.info("Initializing DishGenie backend AI services...")
    
    # 1. Load Vision CNN service
    try:
        vision_svc = get_vision_service()
        logger.info(
            f"VisionService successfully loaded into memory ({len(vision_svc.class_names)} classes mapped)."
        )
    except Exception as exc:
        logger.critical(f"FATAL: Failed to initialize VisionService at startup: {exc}", exc_info=True)
        raise exc

    # 2. Load Recipe Local GenAI service
    try:
        recipe_svc = get_recipe_service()
        logger.info(
            f"RecipeService successfully initialized with model '{recipe_svc.model_name}' on device '{recipe_svc.device}'."
        )
    except Exception as exc:
        logger.critical(f"FATAL: Failed to initialize RecipeService at startup: {exc}", exc_info=True)
        raise exc

    yield

    logger.info("DishGenie backend services shutting down.")


# Create FastAPI application instance
app = FastAPI(
    title="DishGenie API",
    description="Production-ready backend API for DishGenie - CNN Ingredient Detection & Local FLAN-T5 Recipe Services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration allowing React Vite frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(vision_router)
app.include_router(recipe_router)


# Root endpoint
@app.get("/", tags=["System"])
def root():
    return {
        "name": "DishGenie API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }


# Health Check endpoint
@app.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="System and service health check",
    description="Returns the status of the backend API and all registered subservices (Vision & Recipe).",
)
def health_check(
    vision_service: VisionService = Depends(get_vision_service),
    recipe_service: RecipeService = Depends(get_recipe_service),
) -> HealthResponse:
    """
    Health check endpoint reporting API health and individual subsystem status.
    """
    return HealthResponse(
        status="ok",
        services=ServicesStatus(
            vision=ServiceStatus(available=vision_service.is_available),
            recipe=ServiceStatus(available=recipe_service.is_available),
        ),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
