-- Migration: Fix group permission inheritance
-- Issue: Users added to groups do not inherit the permissions defined at the group level.
--
-- Root Cause: The permission resolution query does not join through the
-- group_members table when evaluating a user's effective permissions.
-- Permissions are stored on the group but never propagated to users who
-- are members of that group.
--
-- Fix: Create a view that unions direct user permissions with permissions
-- inherited through group membership, and update the authorization check
-- to use this view.

BEGIN;

-- 1. Create a view that resolves effective permissions for each user,
--    combining direct user permissions with group-inherited permissions.
CREATE OR REPLACE VIEW effective_user_permissions AS
    -- Direct permissions assigned to the user
    SELECT
        up.user_id,
        up.resource_type,
        up.resource_id,
        up.permission,
        'direct' AS source,
        NULL::INTEGER AS source_group_id
    FROM user_permissions up
    WHERE up.deleted_at IS NULL

    UNION ALL

    -- Permissions inherited through group membership
    SELECT
        gm.user_id,
        gp.resource_type,
        gp.resource_id,
        gp.permission,
        'group' AS source,
        gm.group_id AS source_group_id
    FROM group_members gm
    INNER JOIN group_permissions gp ON gp.group_id = gm.group_id
    INNER JOIN groups g ON g.id = gm.group_id
    WHERE gm.deleted_at IS NULL
      AND gp.deleted_at IS NULL
      AND g.deleted_at IS NULL;

-- 2. Create an index to speed up permission lookups through group membership.
CREATE INDEX IF NOT EXISTS idx_group_members_user_group
    ON group_members (user_id, group_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_group_permissions_group_id
    ON group_permissions (group_id)
    WHERE deleted_at IS NULL;

-- 3. Create a function that checks whether a user has a specific permission
--    on a given resource, considering both direct and group-inherited perms.
CREATE OR REPLACE FUNCTION user_has_permission(
    p_user_id INTEGER,
    p_resource_type VARCHAR,
    p_resource_id INTEGER,
    p_permission VARCHAR
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM effective_user_permissions eup
        WHERE eup.user_id = p_user_id
          AND eup.resource_type = p_resource_type
          AND (eup.resource_id = p_resource_id OR eup.resource_id IS NULL)
          AND eup.permission = p_permission
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMIT;
