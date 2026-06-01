-- Fix body_profiles: rename mismatched columns, add missing columns

-- Rename height_cm -> height and change type to DECIMAL(5,2)
ALTER TABLE body_profiles RENAME COLUMN height_cm TO height;
ALTER TABLE body_profiles ALTER COLUMN height TYPE DECIMAL(5,2) USING height::DECIMAL(5,2);
ALTER TABLE body_profiles ALTER COLUMN height SET NOT NULL;

-- Rename weight_kg -> weight
ALTER TABLE body_profiles RENAME COLUMN weight_kg TO weight;
ALTER TABLE body_profiles ALTER COLUMN weight SET NOT NULL;

-- Rename body_fat_percentage -> body_fat and widen precision to DECIMAL(5,2)
ALTER TABLE body_profiles RENAME COLUMN body_fat_percentage TO body_fat;
ALTER TABLE body_profiles ALTER COLUMN body_fat TYPE DECIMAL(5,2);

-- Add columns missing from original schema
ALTER TABLE body_profiles ADD COLUMN IF NOT EXISTS muscle_mass DECIMAL(5,2);
ALTER TABLE body_profiles ADD COLUMN IF NOT EXISTS posture_type VARCHAR(50);
ALTER TABLE body_profiles ADD COLUMN IF NOT EXISTS measurement_date DATE NOT NULL DEFAULT CURRENT_DATE;

-- Index required by BodyProfile entity @Index annotation
CREATE INDEX IF NOT EXISTS idx_body_profile_user_date ON body_profiles(user_id, measurement_date);
