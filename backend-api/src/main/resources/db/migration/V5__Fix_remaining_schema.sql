-- Fix all remaining schema mismatches between V1 migration and JPA entities

-- ============================================================
-- exercises: rename difficulty_level → difficulty, add missing columns
-- ============================================================
ALTER TABLE exercises RENAME COLUMN difficulty_level TO difficulty;
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS description VARCHAR(2000);
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS video_url VARCHAR(500);
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS calories_per_minute DECIMAL(5,2);

-- ============================================================
-- workout_goals: add missing columns
-- ============================================================
ALTER TABLE workout_goals ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE workout_goals ADD COLUMN IF NOT EXISTS description VARCHAR(1000);

-- ============================================================
-- workout_plans: add missing columns, drop unused difficulty_level
-- ============================================================
ALTER TABLE workout_plans ADD COLUMN IF NOT EXISTS agent_generated BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE workout_plans ADD COLUMN IF NOT EXISTS start_date DATE NOT NULL DEFAULT CURRENT_DATE;
ALTER TABLE workout_plans ADD COLUMN IF NOT EXISTS end_date DATE;
ALTER TABLE workout_plans ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE workout_plans DROP COLUMN IF EXISTS difficulty_level;

-- ============================================================
-- workout_plan_items: rename columns, add missing columns
-- ============================================================
ALTER TABLE workout_plan_items RENAME COLUMN duration_seconds TO duration;
ALTER TABLE workout_plan_items RENAME COLUMN sequence_order TO item_order;
ALTER TABLE workout_plan_items ADD COLUMN IF NOT EXISTS rest_time INTEGER;
ALTER TABLE workout_plan_items ADD COLUMN IF NOT EXISTS notes VARCHAR(1000);

-- ============================================================
-- workout_sessions: add missing columns
-- ============================================================
ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS calories_burned DECIMAL(10,2);
ALTER TABLE workout_sessions ADD COLUMN IF NOT EXISTS notes VARCHAR(2000);

-- ============================================================
-- reports: rename report_date → generated_date, add missing columns
-- ============================================================
ALTER TABLE reports RENAME COLUMN report_date TO generated_date;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'COMPLETED';
ALTER TABLE reports ADD COLUMN IF NOT EXISTS file_size BIGINT;
ALTER TABLE reports ADD COLUMN IF NOT EXISTS metadata VARCHAR(1000);
