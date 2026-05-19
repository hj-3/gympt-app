from fastapi import WebSocket
from typing import Dict, Optional
import logging
import json
import asyncio
import base64
import numpy as np
import cv2

from app.config import settings
from app.pose_estimator.mock_estimator import MockPoseEstimator
from app.rules.squat_rule import SquatRule
from app.rules.pushup_rule import PushupRule
from app.feedback.feedback_service import FeedbackService

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Manages WebSocket connections for real-time posture analysis."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.estimator = MockPoseEstimator()
        self.squat_rule = SquatRule(self.estimator)
        self.pushup_rule = PushupRule(self.estimator)
        self.feedback_service = FeedbackService()
        self.frame_count: Dict[str, int] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection."""
        if len(self.connections) >= settings.max_websocket_connections:
            await websocket.close(code=1008, reason="Max connections reached")
            logger.warning(f"Max connections reached, rejected: {session_id}")
            return
        
        await websocket.accept()
        self.connections[session_id] = websocket
        self.frame_count[session_id] = 0
        
        logger.info(f"WebSocket connected: {session_id}")
        
        # Send welcome message
        await self._send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "Ready for posture analysis"
        })
    
    async def disconnect(self, session_id: str):
        """Remove WebSocket connection."""
        if session_id in self.connections:
            del self.connections[session_id]
        if session_id in self.frame_count:
            del self.frame_count[session_id]
        
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def handle_session(self, session_id: str):
        """Handle messages from client."""
        websocket = self.connections.get(session_id)
        if not websocket:
            return
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                message_type = message.get("type")
                
                if message_type == "frame":
                    await self._handle_frame(session_id, message)
                elif message_type == "exercise":
                    await self._handle_exercise_change(session_id, message)
                elif message_type == "ping":
                    await self._send_message(session_id, {"type": "pong"})
                else:
                    logger.warning(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling session {session_id}: {e}")
            raise
    
    async def _handle_frame(self, session_id: str, message: Dict):
        """Process video frame."""
        try:
            # Get frame data (base64 encoded)
            frame_data = message.get("frame")
            exercise = message.get("exercise", "squat")
            
            # Decode frame (simplified for mock)
            if frame_data:
                frame = self._decode_frame(frame_data)
            else:
                # Generate mock frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Estimate pose
            pose_data = await self.estimator.estimate(frame)
            
            # Analyze form based on exercise
            if exercise == "squat":
                analysis = await self.squat_rule.analyze(pose_data)
            elif exercise == "pushup":
                analysis = await self.pushup_rule.analyze(pose_data)
            else:
                analysis = {"error": f"Unknown exercise: {exercise}"}
            
            # Increment frame count
            self.frame_count[session_id] = self.frame_count.get(session_id, 0) + 1
            
            # Generate feedback
            feedback = await self.feedback_service.generate_feedback(analysis)
            
            # Send response
            await self._send_message(session_id, {
                "type": "analysis",
                "session_id": session_id,
                "frame_number": self.frame_count[session_id],
                "score": analysis.get("score", 0),
                "issues": analysis.get("issues", []),
                "feedback": feedback,
                "confidence": pose_data.get("confidence", 0)
            })
            
            # Publish to Redis if score is low
            if analysis.get("score", 10) < settings.feedback_threshold_score:
                await self.feedback_service.publish_feedback(
                    session_id=session_id,
                    analysis=analysis,
                    feedback=feedback
                )
        
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            await self._send_message(session_id, {
                "type": "error",
                "message": str(e)
            })
    
    async def _handle_exercise_change(self, session_id: str, message: Dict):
        """Handle exercise type change."""
        exercise = message.get("exercise")
        logger.info(f"Session {session_id} changed exercise to: {exercise}")
        
        await self._send_message(session_id, {
            "type": "exercise_changed",
            "exercise": exercise,
            "message": f"Now analyzing {exercise} form"
        })
    
    async def _send_message(self, session_id: str, message: Dict):
        """Send message to client."""
        websocket = self.connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
    
    def _decode_frame(self, frame_data: str) -> np.ndarray:
        """Decode base64 frame to numpy array."""
        try:
            # Remove data URL prefix if present
            if "base64," in frame_data:
                frame_data = frame_data.split("base64,")[1]
            
            # Decode base64
            img_bytes = base64.b64decode(frame_data)
            
            # Convert to numpy array
            nparr = np.frombuffer(img_bytes, np.uint8)
            
            # Decode image
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return frame
        except Exception as e:
            logger.error(f"Error decoding frame: {e}")
            # Return black frame on error
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    @property
    def active_connections(self) -> int:
        """Get number of active connections."""
        return len(self.connections)
