-- V8: Fix user deletion to properly cascade-delete all related data,
--     and fix the email unique index that V2 failed to drop (used DROP CONSTRAINT
--     instead of DROP INDEX on a non-constraint index).

-- Fix email uniqueness: cognitoSub is the real unique identifier, not email.
-- A re-registered user may reuse the same email with a new cognitoSub.
DROP INDEX IF EXISTS idx_user_email;
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);

-- Add ON DELETE CASCADE so that deleting a user automatically removes all
-- their data without needing application-level coordination.

-- body_profiles
ALTER TABLE body_profiles
    DROP CONSTRAINT IF EXISTS body_profiles_user_id_fkey;
ALTER TABLE body_profiles
    ADD CONSTRAINT body_profiles_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- workout_sessions
ALTER TABLE workout_sessions
    DROP CONSTRAINT IF EXISTS workout_sessions_user_id_fkey;
ALTER TABLE workout_sessions
    ADD CONSTRAINT workout_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- workout_goals
ALTER TABLE workout_goals
    DROP CONSTRAINT IF EXISTS workout_goals_user_id_fkey;
ALTER TABLE workout_goals
    ADD CONSTRAINT workout_goals_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- workout_plan_items must cascade from workout_plans before plans cascade from users
ALTER TABLE workout_plan_items
    DROP CONSTRAINT IF EXISTS workout_plan_items_workout_plan_id_fkey;
ALTER TABLE workout_plan_items
    ADD CONSTRAINT workout_plan_items_workout_plan_id_fkey
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE;

-- workout_plans
ALTER TABLE workout_plans
    DROP CONSTRAINT IF EXISTS workout_plans_user_id_fkey;
ALTER TABLE workout_plans
    ADD CONSTRAINT workout_plans_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- reports
ALTER TABLE reports
    DROP CONSTRAINT IF EXISTS reports_user_id_fkey;
ALTER TABLE reports
    ADD CONSTRAINT reports_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- workout_recommendations already has ON DELETE CASCADE from V3, no change needed.
