"""
GYMPT Posture Analysis Service - Real-time pose estimation and analysis
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .config.settings import settings
from .api.routes import router as api_router
from .services.model_loader import load_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENV}")
    print(f"GPU Enabled: {settings.GPU_ENABLED}")

    # Load ML models
    print("Loading pose estimation models...")
    app.state.models = await load_models()
    print("Models loaded successfully")

    yield

    # Shutdown
    print(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description="Real-time posture analysis using computer vision",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix="/api/v1")

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "gpu_enabled": settings.GPU_ENABLED,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    # Check if models are loaded
    if not hasattr(app.state, "models"):
        return {"status": "not_ready", "reason": "models_not_loaded"}

    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.ENV == "local",
    )
