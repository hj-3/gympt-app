# Posture Analysis Service - Unit Tests

## Structure

```
unit/
├── test_pose_detector.py       # MediaPipe pose detection
├── test_form_analyzer.py       # Exercise form analysis
├── test_rep_counter.py         # Rep counting logic
└── test_angle_calculator.py    # Angle calculations
```

## Test Fixtures

Sample poses stored in `tests/fixtures/poses/`:
- `squat_correct.json` - Correct squat form landmarks
- `squat_knee_valgus.json` - Knee valgus issue
- `deadlift_rounded_back.json` - Form issue

## Running

```bash
pytest tests/unit/ -v --cov=app.analysis
```
