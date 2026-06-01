from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from prometheus_client import make_asgi_app

from app.config import settings
from app.streaming.websocket_handler import WebSocketHandler
from app.clients.redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket connection manager
ws_handler = WebSocketHandler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting {settings.service_name} in {settings.app_env} environment")
    logger.info(f"Model type: {settings.model_type}, GPU: {settings.should_use_gpu}")
    logger.info(f"KVS Mock: {settings.enable_kvs_mock}")
    
    # Initialize connections
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down posture-analysis-service")
    await redis_client.close()


app = FastAPI(
    title="GYMPT Posture Analysis Service",
    description="Real-time posture analysis using computer vision",
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
        "model_type": settings.model_type,
        "gpu_enabled": settings.should_use_gpu,
        "kvs_mock": settings.enable_kvs_mock,
        "active_sessions": ws_handler.active_connections
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "GYMPT Posture Analysis Service",
        "version": "0.1.0",
        "websocket": "/ws/posture/{session_id}"
    }


@app.websocket("/ws/posture/{session_id}")
async def posture_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time posture analysis.
    
    Client sends video frames, server responds with posture feedback.
    """
    await ws_handler.connect(websocket, session_id)
    
    try:
        await ws_handler.handle_session(session_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        await ws_handler.disconnect(session_id)
