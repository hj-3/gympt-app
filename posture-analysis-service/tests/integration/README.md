# Posture Analysis Service - Integration Tests

## Structure

```
integration/
├── test_video_processing.py    # End-to-end video analysis
├── test_kvs_integration.py     # Kinesis Video Streams
└── test_event_publishing.py    # SQS/DynamoDB publishing
```

## Test Videos

Sample videos in `tests/fixtures/videos/`:
- `squat_10reps.mp4` - 10 reps of squats
- `pushup_form_issue.mp4` - Push-ups with form issues

## Running

```bash
pytest tests/integration/ -v --video-samples=tests/fixtures/videos/
```
