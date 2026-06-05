from fastapi import WebSocket
from typing import Dict, Optional
import logging
import json
import base64
import numpy as np
import cv2

from app.config import settings
from app.pose_estimator.base import PoseEstimator
from app.pose_estimator.mediapipe_estimator import MediaPipePoseEstimator
from app.pose_estimator.mock_estimator import MockPoseEstimator
from app.rules.squat_rule import SquatRule
from app.rules.pushup_rule import PushupRule
from app.rules.lunge_rule import LungeRule
from app.rules.plank_rule import PlankRule
from app.counting.rep_counter import RepCounter
from app.feedback.feedback_service import FeedbackService

logger = logging.getLogger(__name__)


class _SessionContext:
    """Per-session pose estimator, rules and rep counter.

    A dedicated estimator per session is required because MediaPipe Pose keeps
    temporal tracking state internally; sharing one across concurrent sessions
    would mix up landmarks between users.
    """

    def __init__(self, exercise: str):
        self.estimator = _build_estimator()
        self.exercise = exercise
        self.squat_rule = SquatRule(self.estimator)
        self.pushup_rule = PushupRule(self.estimator)
        self.lunge_rule = LungeRule(self.estimator)
        self.plank_rule = PlankRule(self.estimator)
        self.rep_counter = RepCounter(
            exercise,
            settings.rep_counter_thresholds.get(exercise),
        )

    def set_exercise(self, exercise: str):
        if exercise == self.exercise:
            return
        self.exercise = exercise
        self.rep_counter = RepCounter(
            exercise,
            settings.rep_counter_thresholds.get(exercise),
        )

    async def analyze(self, pose_data: Dict) -> Dict:
        if self.exercise == "squat":
            return await self.squat_rule.analyze(pose_data)
        if self.exercise == "pushup":
            return await self.pushup_rule.analyze(pose_data)
        if self.exercise == "lunge":
            return await self.lunge_rule.analyze(pose_data)
        if self.exercise == "plank":
            return await self.plank_rule.analyze(pose_data)
        return {"exercise": self.exercise, "score": 0, "issues": [],
                "error": f"Unknown exercise: {self.exercise}"}

    def close(self):
        # MediaPipe estimator holds native resources
        if hasattr(self.estimator, "__del__"):
            try:
                self.estimator.__del__()
            except Exception:
                pass


def _build_estimator() -> PoseEstimator:
    """Create the configured pose estimator. Defaults to real MediaPipe."""
    if settings.model_type == "mock":
        logger.warning("Using MockPoseEstimator (model_type=mock)")
        return MockPoseEstimator()
    return MediaPipePoseEstimator(enable_gpu=settings.should_use_gpu)


class WebSocketHandler:
    """Manages WebSocket connections for real-time posture analysis."""

    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.sessions: Dict[str, _SessionContext] = {}
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
        self.sessions[session_id] = _SessionContext(exercise="squat")
        self.frame_count[session_id] = 0

        logger.info(f"WebSocket connected: {session_id}")

        await self._send_message(session_id, {
            "type": "connected",
            "session_id": session_id,
            "message": "Ready for posture analysis"
        })

    async def disconnect(self, session_id: str):
        """Remove WebSocket connection and release pose resources."""
        self.connections.pop(session_id, None)
        self.frame_count.pop(session_id, None)
        ctx = self.sessions.pop(session_id, None)
        if ctx:
            ctx.close()

        logger.info(f"WebSocket disconnected: {session_id}")

    async def handle_session(self, session_id: str):
        """Handle messages from client."""
        websocket = self.connections.get(session_id)
        if not websocket:
            return

        try:
            while True:
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
        """Process a real video frame through MediaPipe pose estimation."""
        ctx = self.sessions.get(session_id)
        if not ctx:
            return

        try:
            frame_data = message.get("frame")
            exercise = message.get("exercise")
            if exercise:
                ctx.set_exercise(exercise)

            # A real frame is required — no synthetic fallback.
            if not frame_data:
                await self._send_message(session_id, {
                    "type": "error",
                    "message": "No frame data received",
                })
                return

            frame = self._decode_frame(frame_data)
            if frame is None:
                await self._send_message(session_id, {
                    "type": "error",
                    "message": "Failed to decode frame",
                })
                return

            # Real pose estimation
            pose_data = await ctx.estimator.estimate(frame)
            confidence = pose_data.get("confidence", 0.0)
            keypoints = pose_data.get("keypoints", {})

            self.frame_count[session_id] = self.frame_count.get(session_id, 0) + 1

            # No person detected in this frame
            if confidence <= 0.0 or not keypoints:
                await self._send_message(session_id, {
                    "type": "analysis",
                    "session_id": session_id,
                    "frame_number": self.frame_count[session_id],
                    "pose_detected": False,
                    "landmarks": pose_data.get("landmarks", []),
                    "score": 0,
                    "issues": [],
                    "angles": {},
                    "rep_count": ctx.rep_counter.total_reps,
                    "confidence": confidence,
                    "feedback": {"overall": "사람이 감지되지 않습니다. 전신이 화면에 보이도록 조정하세요.",
                                 "priority": "info", "corrections": []},
                })
                return

            # Form analysis + rep counting from real keypoints
            analysis = await ctx.analyze(pose_data)
            rep_result = ctx.rep_counter.count_reps(keypoints)
            angles = self._compute_angles(ctx, ctx.exercise, keypoints)

            feedback = await self.feedback_service.generate_feedback(analysis)

            await self._send_message(session_id, {
                "type": "analysis",
                "session_id": session_id,
                "frame_number": self.frame_count[session_id],
                "pose_detected": True,
                "landmarks": pose_data.get("landmarks", []),
                "score": analysis.get("score", 0),
                "issues": analysis.get("issues", []),
                "angles": angles,
                "rep_count": rep_result.total_reps,
                "rep_state": rep_result.current_state.value,
                "confidence": confidence,
                "feedback": feedback,
            })

            # Publish low-score events for downstream consumers
            if analysis.get("score", 10) < settings.feedback_threshold_score:
                await self.feedback_service.publish_feedback(
                    session_id=session_id,
                    analysis=analysis,
                    feedback=feedback,
                )

        except Exception as e:
            logger.error(f"Error processing frame: {e}", exc_info=True)
            await self._send_message(session_id, {
                "type": "error",
                "message": str(e),
            })

    def _compute_angles(self, ctx: _SessionContext, exercise: str, keypoints: Dict) -> Dict[str, float]:
        """Compute real joint angles from detected keypoints for display."""
        est = ctx.estimator

        def angle(a: str, b: str, c: str) -> Optional[float]:
            pa, pb, pc = keypoints.get(a), keypoints.get(b), keypoints.get(c)
            if not all([pa, pb, pc]):
                return None
            return round(est.calculate_angle(pa, pb, pc), 1)

        angles: Dict[str, float] = {}
        if exercise == "squat":
            v = angle("left_hip", "left_knee", "left_ankle")
            if v is not None:
                angles["무릎 각도"] = v
            v = angle("left_shoulder", "left_hip", "left_knee")
            if v is not None:
                angles["고관절 각도"] = v
        elif exercise == "pushup":
            v = angle("left_shoulder", "left_elbow", "left_wrist")
            if v is not None:
                angles["팔꿈치 각도"] = v
            v = angle("left_shoulder", "left_hip", "left_ankle")
            if v is not None:
                angles["몸통 각도"] = v
        elif exercise == "lunge":
            v = angle("left_hip", "left_knee", "left_ankle")
            if v is not None:
                angles["앞 무릎 각도"] = v
        elif exercise == "plank":
            v = angle("left_shoulder", "left_hip", "left_ankle")
            if v is not None:
                angles["몸통 각도"] = v
        return angles

    async def _handle_exercise_change(self, session_id: str, message: Dict):
        """Handle exercise type change."""
        exercise = message.get("exercise")
        ctx = self.sessions.get(session_id)
        if ctx and exercise:
            ctx.set_exercise(exercise)
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

    def _decode_frame(self, frame_data: str) -> Optional[np.ndarray]:
        """Decode base64 frame to numpy array. Returns None on failure."""
        try:
            if "base64," in frame_data:
                frame_data = frame_data.split("base64,")[1]

            img_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            logger.error(f"Error decoding frame: {e}")
            return None

    @property
    def active_connections(self) -> int:
        """Get number of active connections."""
        return len(self.connections)
