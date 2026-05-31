from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from prometheus_client import make_asgi_app

from app.config import settings
from app.routers import workout_recommendation, posture_feedback, report_generation
from app.clients.redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.service_name} in {settings.app_env} environment")
    
    # Initialize connections
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down agent-service")
    await redis_client.close()


app = FastAPI(
    title="GYMPT Agent Service",
    description="AI Agent service using Amazon Bedrock for workout recommendations",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(workout_recommendation.router, prefix="/agent", tags=["Workout"])
app.include_router(posture_feedback.router, prefix="/agent", tags=["Posture"])
app.include_router(report_generation.router, prefix="/agent", tags=["Report"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "environment": settings.app_env,
        "bedrock_mock": settings.enable_bedrock_mock
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "GYMPT Agent Service",
        "version": "0.1.0",
        "docs": "/docs"
    }
