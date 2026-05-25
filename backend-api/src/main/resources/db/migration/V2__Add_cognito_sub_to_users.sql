-- Migration for Cognito integration
-- Add cognito_sub column and make password nullable

-- Add cognito_sub column (nullable initially for migration)
ALTER TABLE users ADD COLUMN IF NOT EXISTS cognito_sub VARCHAR(255);

-- Make password nullable (authentication handled by Cognito)
ALTER TABLE users ALTER COLUMN password DROP NOT NULL;

-- Create unique index on cognito_sub (will be enforced after data migration)
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_cognito_sub ON users(cognito_sub) WHERE cognito_sub IS NOT NULL;

-- Drop old email unique constraint and create non-unique index
ALTER TABLE users DROP CONSTRAINT IF EXISTS idx_user_email;
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
