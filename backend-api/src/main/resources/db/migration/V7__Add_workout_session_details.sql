-- Add exercise details to workout_sessions for report & dashboard data
ALTER TABLE workout_sessions
    ADD COLUMN IF NOT EXISTS exercise_type       VARCHAR(50),
    ADD COLUMN IF NOT EXISTS exercise_name       VARCHAR(100),
    ADD COLUMN IF NOT EXISTS total_reps          INTEGER,
    ADD COLUMN IF NOT EXISTS avg_posture_score   NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS recommendation_id   UUID;
