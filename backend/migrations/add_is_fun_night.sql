-- Migration: Add is_fun_night and target_levels columns to meeting_plans
ALTER TABLE meeting_plans ADD COLUMN IF NOT EXISTS is_fun_night BOOLEAN DEFAULT FALSE;
ALTER TABLE meeting_plans ADD COLUMN IF NOT EXISTS target_levels INTEGER[];