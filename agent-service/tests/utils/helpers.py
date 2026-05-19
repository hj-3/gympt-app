"""
Test helper functions and data generators.
"""
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


def generate_user_id() -> str:
    """Generate a random user ID."""
    return str(uuid.uuid4())


def generate_workout_request(
    goal: str = None,
    fitness_level: str = None,
    days_per_week: int = None,
    with_equipment: bool = True,
    with_injuries: bool = False
) -> Dict[str, Any]:
    """Generate a random workout recommendation request."""
    goals = ["weight_loss", "muscle_gain", "endurance", "flexibility", "general_fitness"]
    levels = ["beginner", "intermediate", "advanced", "expert"]
    equipment = ["barbell", "dumbbell", "bench", "squat_rack", "pull_up_bar", "kettlebell"]

    request = {
        "user_id": generate_user_id(),
        "goal": goal or random.choice(goals),
        "fitness_level": fitness_level or random.choice(levels),
        "days_per_week": days_per_week or random.randint(3, 6),
        "equipment_available": random.sample(equipment, k=random.randint(0, 4)) if with_equipment else [],
        "injuries_or_limitations": None
    }

    if with_injuries:
        injuries = [
            "Lower back pain",
            "Knee issues",
            "Shoulder mobility limitations",
            "Previous ankle injury",
            "Wrist pain"
        ]
        request["injuries_or_limitations"] = random.choice(injuries)

    return request


def generate_posture_request(
    exercise: str = None,
    score: float = None,
    num_issues: int = 2
) -> Dict[str, Any]:
    """Generate a random posture feedback request."""
    exercises = ["squat", "deadlift", "bench_press", "overhead_press", "row", "plank", "pushup"]
    all_issues = [
        "knee_valgus",
        "insufficient_depth",
        "rounded_back",
        "improper_hip_hinge",
        "elbow_flare",
        "hip_sag",
        "head_position",
        "foot_position"
    ]

    return {
        "session_id": f"session-{uuid.uuid4()}",
        "exercise_name": exercise or random.choice(exercises),
        "posture_score": score or round(random.uniform(4.0, 9.5), 1),
        "detected_issues": random.sample(all_issues, k=min(num_issues, len(all_issues))),
        "frame_data": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "landmarks": {}
        }
    }


def generate_report_request(
    days_back: int = 7,
    include_sections: List[str] = None
) -> Dict[str, Any]:
    """Generate a random report generation request."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    return {
        "user_id": generate_user_id(),
        "period_start": start_date.strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d"),
        "include_sections": include_sections or ["summary", "workouts", "progress", "recommendations"]
    }


def generate_user_profile(
    with_optional_fields: bool = True
) -> Dict[str, Any]:
    """Generate a random user profile."""
    profile = {
        "user_id": generate_user_id(),
        "name": fake.name(),
        "email": fake.email(),
    }

    if with_optional_fields:
        profile.update({
            "age": random.randint(18, 65),
            "gender": random.choice(["male", "female", "other"]),
            "fitness_experience": random.choice(["beginner", "intermediate", "advanced"]),
            "created_at": fake.date_time_this_year().isoformat() + "Z"
        })

    return profile


def generate_body_profile() -> Dict[str, Any]:
    """Generate a random body profile."""
    return {
        "user_id": generate_user_id(),
        "height_cm": round(random.uniform(150, 200), 1),
        "weight_kg": round(random.uniform(50, 120), 1),
        "body_fat_percentage": round(random.uniform(10, 35), 1),
        "muscle_mass_kg": round(random.uniform(20, 50), 1),
        "measurements": {
            "chest_cm": random.randint(80, 120),
            "waist_cm": random.randint(60, 100),
            "hips_cm": random.randint(80, 120)
        },
        "last_updated": datetime.utcnow().isoformat() + "Z"
    }


def generate_workout_goal() -> Dict[str, Any]:
    """Generate a random workout goal."""
    goal_types = ["weight_loss", "muscle_gain", "strength", "endurance"]

    return {
        "goal_id": generate_user_id(),
        "user_id": generate_user_id(),
        "goal_type": random.choice(goal_types),
        "target_value": round(random.uniform(60, 100), 1),
        "current_value": round(random.uniform(50, 90), 1),
        "deadline": (datetime.utcnow() + timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
        "status": random.choice(["active", "completed", "paused"]),
        "created_at": fake.date_time_this_year().isoformat() + "Z"
    }


def generate_mock_bedrock_response(
    content_type: str = "workout"
) -> Dict[str, Any]:
    """Generate a mock Bedrock response."""
    content_templates = {
        "workout": """Based on your profile, here's a personalized workout plan:

**Week 1-4: Foundation Phase**
- Monday: Upper Body Strength
- Wednesday: Lower Body Strength
- Friday: Full Body Conditioning

**Progression:**
- Increase weight by 5% every 2 weeks
- Focus on form and consistency""",
        "posture": """Form Analysis:

**Good Points:**
- Core engagement is strong
- Upper body alignment correct

**Areas for Improvement:**
- Slight knee valgus detected
- Aim for deeper squat depth

**Corrections:**
- Push knees outward
- Focus on ankle mobility""",
        "report": """Weekly Progress Summary:

**Achievements:**
- Completed 4/5 planned workouts
- Squat PR: +10 lbs
- Consistency: 80%

**Recommendations:**
- Increase training volume
- Focus on nutrition
- Add mobility work"""
    }

    return {
        "content": content_templates.get(content_type, "Mock response"),
        "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "usage": {
            "input_tokens": random.randint(50, 200),
            "output_tokens": random.randint(100, 500)
        },
        "stop_reason": "end_turn"
    }


def generate_cache_key(
    endpoint: str,
    user_id: str,
    params: Dict[str, Any] = None
) -> str:
    """Generate a cache key for testing."""
    import hashlib
    import json

    param_str = json.dumps(params or {}, sort_keys=True)
    param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]

    return f"{endpoint}:{user_id}:{param_hash}"


def wait_for_condition(
    condition_func,
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """Wait for a condition to become true."""
    import time

    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)

    return False


def assert_within_range(value: float, expected: float, tolerance: float = 0.1) -> None:
    """Assert value is within tolerance of expected value."""
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)

    assert lower <= value <= upper, \
        f"Value {value} not within {tolerance*100}% of {expected}"


def create_test_data_batch(count: int, data_type: str = "workout") -> List[Dict[str, Any]]:
    """Create a batch of test data."""
    generators = {
        "workout": generate_workout_request,
        "posture": generate_posture_request,
        "report": generate_report_request,
        "user_profile": generate_user_profile,
        "body_profile": generate_body_profile
    }

    generator = generators.get(data_type, generate_workout_request)
    return [generator() for _ in range(count)]


def simulate_api_latency(min_ms: int = 50, max_ms: int = 200) -> None:
    """Simulate API latency for testing."""
    import time
    import random

    latency = random.randint(min_ms, max_ms) / 1000.0
    time.sleep(latency)
