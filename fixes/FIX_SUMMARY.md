# Fix: Group Permissions and Deletion Issues

## Issue 1 – Users Do Not Inherit Permissions from Group

**Reported behavior:** After creating a user group, assigning permissions to it,
and adding users (e.g., test@vntt.com.vn), the users do not inherit or apply the
permissions defined at the group level. Users cannot see VMs or create new VMs.

**Root cause:** The authorization check only evaluates direct user permissions
(`user_permissions` table) and does not resolve permissions inherited through
group membership (`group_members` + `group_permissions` tables).

**Fix applied:**

1. **Database migration** (`migrations/001_fix_group_permission_inheritance.sql`):
   - Creates `effective_user_permissions` view that unions direct user permissions
     with group-inherited permissions via `group_members` and `group_permissions`.
   - Adds indexes on `group_members` and `group_permissions` for performance.
   - Creates a `user_has_permission()` function that checks both direct and
     inherited permissions.

2. **Service layer** (`services/permission_service.py`):
   - `check_permission()` queries the unified view for authorization checks.
   - `get_accessible_resources()` resolves which resources a user can access.
   - `user_can_create()` checks create permission through group inheritance.

## Issue 2 – Group Name Still Exists After Deletion

**Reported behavior:** After deleting a group (e.g., 'QTDC'), creating a new
group with the same name fails. The system reports the name already exists.

**Root cause:** The unique constraint on `groups.name` does not exclude
soft-deleted records (`deleted_at IS NOT NULL`). When a group is soft-deleted,
its name still occupies the unique constraint, blocking reuse.

**Fix applied:**

1. **Database migration** (`migrations/002_fix_group_soft_delete.sql`):
   - Drops the existing unconditional unique constraint on `groups.name`.
   - Creates a partial unique index that only enforces uniqueness among active
     (non-deleted) groups: `WHERE deleted_at IS NULL`.
   - Cleans up any existing soft-deleted groups that might conflict.

2. **Service layer** (`services/group_service.py`):
   - `create_group()` only checks for name conflicts among active groups.
   - `delete_group()` performs soft-delete; the name is immediately reusable.
   - `hard_delete_group()` available as an alternative for full removal.

## How to Apply

1. Run the database migrations in order:
   ```sql
   \i fixes/migrations/001_fix_group_permission_inheritance.sql
   \i fixes/migrations/002_fix_group_soft_delete.sql
   ```

2. Update the application's permission checking and group management code to use
   the new service layer or equivalent logic.

## Tests

Run the test suite to verify both fixes:
```bash
python fixes/tests/test_permission_inheritance.py
python fixes/tests/test_group_deletion.py
```
