-- Create workout_recommendations table
CREATE TABLE IF NOT EXISTS workout_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    interaction_id VARCHAR(255),
    goal VARCHAR(100),
    fitness_level VARCHAR(50),
    days_per_week INTEGER,
    equipment_available TEXT,
    injuries_or_limitations TEXT,
    model_used VARCHAR(255),
    session_id VARCHAR(255),
    height DOUBLE PRECISION,
    weight DOUBLE PRECISION,
    body_fat DOUBLE PRECISION,
    muscle_mass DOUBLE PRECISION,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create index on user_id and created_at for efficient queries
CREATE INDEX idx_workout_recommendations_user_created ON workout_recommendations(user_id, created_at DESC);

-- Create index on interaction_id for tracking
CREATE INDEX idx_workout_recommendations_interaction ON workout_recommendations(interaction_id);
