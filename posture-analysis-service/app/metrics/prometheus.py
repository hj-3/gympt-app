"""Prometheus metrics for posture analysis service."""
from prometheus_client import Counter, Histogram, Gauge

# Frame processing metrics
frames_processed_total = Counter(
    "gympt_posture_frames_processed_total",
    "Total number of frames processed",
    ["exercise_type", "model_type"]
)

frame_processing_duration = Histogram(
    "gympt_posture_frame_processing_duration_seconds",
    "Frame processing duration in seconds",
    ["exercise_type"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Pose estimation metrics
pose_estimation_errors_total = Counter(
    "gympt_posture_pose_estimation_errors_total",
    "Total number of pose estimation errors",
    ["model_type", "error_type"]
)

# Rep counting metrics
rep_count_total = Counter(
    "gympt_posture_rep_count_total",
    "Total number of reps counted",
    ["exercise_type", "user_id"]
)

# Posture score metrics
posture_score_distribution = Histogram(
    "gympt_posture_score_distribution",
    "Distribution of posture scores (0-10)",
    ["exercise_type"],
    buckets=[0, 2, 4, 6, 7, 8, 9, 10]
)

# Session metrics
active_sessions_gauge = Gauge(
    "gympt_posture_active_sessions",
    "Number of currently active posture analysis sessions",
    ["exercise_type"]
)

# AWS integration metrics
dynamodb_writes_total = Counter(
    "gympt_posture_dynamodb_writes_total",
    "Total number of DynamoDB write operations",
    ["status"]  # success, error
)

s3_uploads_total = Counter(
    "gympt_posture_s3_uploads_total",
    "Total number of S3 upload operations",
    ["upload_type", "status"]  # upload_type: results, frames; status: success, error
)

sqs_publishes_total = Counter(
    "gympt_posture_sqs_publishes_total",
    "Total number of SQS publish operations",
    ["event_type", "status"]  # event_type: completion, issue, milestone
)
