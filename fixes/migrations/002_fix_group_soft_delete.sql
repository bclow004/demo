-- Migration: Fix group name reuse after deletion
-- Issue: After deleting a group, creating a new group with the same name fails
-- because the system reports the name already exists.
--
-- Root Cause: The unique constraint on the groups table's `name` column does
-- not account for soft-deleted records. When a group is soft-deleted
-- (deleted_at is set), its name still occupies the unique constraint,
-- preventing reuse.
--
-- Fix: Replace the unconditional unique constraint with a partial unique index
-- that only enforces uniqueness among non-deleted (active) groups.

BEGIN;

-- 1. Drop the existing unique constraint on group name.
--    (Try both common constraint naming conventions)
DO $$
BEGIN
    -- Attempt to drop constraint named 'groups_name_key'
    ALTER TABLE groups DROP CONSTRAINT IF EXISTS groups_name_key;
    -- Attempt to drop constraint named 'uq_groups_name'
    ALTER TABLE groups DROP CONSTRAINT IF EXISTS uq_groups_name;
    -- Attempt to drop constraint named 'unique_group_name'
    ALTER TABLE groups DROP CONSTRAINT IF EXISTS unique_group_name;
    -- Attempt to drop index named 'idx_groups_name_unique'
    DROP INDEX IF EXISTS idx_groups_name_unique;
    -- Attempt to drop index named 'groups_name_idx'
    DROP INDEX IF EXISTS groups_name_idx;
END $$;

-- 2. Create a partial unique index that only applies to active (non-deleted) groups.
--    This allows deleted group names to be reused while still preventing
--    duplicate names among active groups.
CREATE UNIQUE INDEX idx_groups_name_unique_active
    ON groups (name)
    WHERE deleted_at IS NULL;

-- 3. Clean up any existing soft-deleted groups that might have duplicate names
--    by appending a deletion timestamp suffix. This prevents issues if the
--    migration is run on a database with existing soft-deleted duplicates.
UPDATE groups
SET name = name || '_deleted_' || EXTRACT(EPOCH FROM deleted_at)::TEXT
WHERE deleted_at IS NOT NULL
  AND EXISTS (
      SELECT 1
      FROM groups g2
      WHERE g2.name = groups.name
        AND g2.id != groups.id
        AND g2.deleted_at IS NULL
  );

COMMIT;
