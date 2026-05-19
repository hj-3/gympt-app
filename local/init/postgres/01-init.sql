-- GYMPT Database Initialization Script

-- Create test database
CREATE DATABASE gympt_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE gympt TO gympt_user;
GRANT ALL PRIVILEGES ON DATABASE gympt_test TO gympt_user;

-- Connect to gympt database
\c gympt;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create workout_types table
CREATE TABLE IF NOT EXISTS workout_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_workout_types_category ON workout_types(category);

-- Insert default workout types
INSERT INTO workout_types (id, name, description, category) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Push-ups', 'Upper body strength training', 'STRENGTH'),
('550e8400-e29b-41d4-a716-446655440002', 'Squats', 'Lower body strength training', 'STRENGTH'),
('550e8400-e29b-41d4-a716-446655440003', 'Running', 'Cardiovascular exercise', 'CARDIO'),
('550e8400-e29b-41d4-a716-446655440004', 'Yoga', 'Flexibility and balance', 'FLEXIBILITY'),
('550e8400-e29b-41d4-a716-446655440005', 'Plank', 'Core strengthening', 'CORE')
ON CONFLICT (id) DO NOTHING;

-- Connect to test database
\c gympt_test;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create same schema for test database
CREATE TABLE IF NOT EXISTS workout_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
