-- Migration: Add soft delete columns
ALTER TABLE term_plans ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;
ALTER TABLE meeting_plans ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Index for efficient querying of soft-deleted items
CREATE INDEX IF NOT EXISTS idx_term_plans_deleted ON term_plans(deleted_at);
CREATE INDEX IF NOT EXISTS idx_meeting_plans_deleted ON meeting_plans(deleted_at);
