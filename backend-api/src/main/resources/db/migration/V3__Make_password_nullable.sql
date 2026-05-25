-- Make password column nullable for Cognito authentication
-- Users authenticate via Cognito, so password is not stored in database

ALTER TABLE users ALTER COLUMN password DROP NOT NULL;
