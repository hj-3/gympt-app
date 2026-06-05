-- Add structured KVS-trackable targets to workout recommendations.
-- Stored as JSON text: [{"exercise":"squat","sets":3,"reps":12}]
ALTER TABLE workout_recommendations
    ADD COLUMN IF NOT EXISTS target_exercises TEXT;
