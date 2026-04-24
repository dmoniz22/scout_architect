-- Migration: Add is_fun_night column to meeting_plans
ALTER TABLE meeting_plans ADD COLUMN IF NOT EXISTS is_fun_night BOOLEAN DEFAULT FALSE;