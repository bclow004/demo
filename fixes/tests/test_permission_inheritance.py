"""
Tests for group permission inheritance fix.

Verifies that users correctly inherit permissions from groups they belong to.
"""

import sqlite3
from unittest.mock import MagicMock


def create_test_db():
    """Create an in-memory SQLite database with the required schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT,
            deleted_at TEXT DEFAULT NULL
        );

        CREATE TABLE group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TEXT,
            deleted_at TEXT DEFAULT NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id)
        );

        CREATE TABLE user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id INTEGER,
            permission TEXT NOT NULL,
            deleted_at TEXT DEFAULT NULL
        );

        CREATE TABLE group_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id INTEGER,
            permission TEXT NOT NULL,
            deleted_at TEXT DEFAULT NULL,
            FOREIGN KEY (group_id) REFERENCES groups(id)
        );

        -- The fix: create the effective_user_permissions view
        CREATE VIEW effective_user_permissions AS
            SELECT
                up.user_id,
                up.resource_type,
                up.resource_id,
                up.permission,
                'direct' AS source,
                NULL AS source_group_id
            FROM user_permissions up
            WHERE up.deleted_at IS NULL

            UNION ALL

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
    """)

    conn.commit()
    return conn


def test_user_inherits_group_permissions():
    """User should see VMs when their group has view permission."""
    conn = create_test_db()
    cursor = conn.cursor()

    # Create a group
    cursor.execute(
        "INSERT INTO groups (id, name, created_at) VALUES (1, 'VM Operators', '2024-01-01')"
    )

    # Assign VM view permission to the group
    cursor.execute(
        "INSERT INTO group_permissions (group_id, resource_type, resource_id, permission) "
        "VALUES (1, 'vm', NULL, 'view')"
    )

    # Add user (id=100, representing test@vntt.com.vn) to the group
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, created_at) "
        "VALUES (1, 100, '2024-01-01')"
    )
    conn.commit()

    # Check that the user inherits the group's VM view permission
    result = cursor.execute(
        "SELECT * FROM effective_user_permissions WHERE user_id = 100 AND resource_type = 'vm'"
    ).fetchall()

    assert len(result) == 1, f"Expected 1 permission, got {len(result)}"
    assert result[0]["permission"] == "view"
    assert result[0]["source"] == "group"
    assert result[0]["source_group_id"] == 1
    print("PASS: User inherits group permissions")


def test_user_inherits_create_permission():
    """User should be able to create VMs when their group has create permission."""
    conn = create_test_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO groups (id, name, created_at) VALUES (1, 'VM Admins', '2024-01-01')"
    )
    cursor.execute(
        "INSERT INTO group_permissions (group_id, resource_type, resource_id, permission) "
        "VALUES (1, 'vm', NULL, 'create')"
    )
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, created_at) "
        "VALUES (1, 100, '2024-01-01')"
    )
    conn.commit()

    result = cursor.execute(
        "SELECT * FROM effective_user_permissions "
        "WHERE user_id = 100 AND resource_type = 'vm' AND permission = 'create'"
    ).fetchall()

    assert len(result) == 1, f"Expected 1 create permission, got {len(result)}"
    print("PASS: User inherits create permission from group")


def test_deleted_group_permissions_not_inherited():
    """User should NOT inherit permissions from a soft-deleted group."""
    conn = create_test_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO groups (id, name, created_at, deleted_at) "
        "VALUES (1, 'Deleted Group', '2024-01-01', '2024-06-01')"
    )
    cursor.execute(
        "INSERT INTO group_permissions (group_id, resource_type, resource_id, permission) "
        "VALUES (1, 'vm', NULL, 'view')"
    )
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, created_at) "
        "VALUES (1, 100, '2024-01-01')"
    )
    conn.commit()

    result = cursor.execute(
        "SELECT * FROM effective_user_permissions WHERE user_id = 100"
    ).fetchall()

    assert len(result) == 0, f"Expected 0 permissions from deleted group, got {len(result)}"
    print("PASS: Deleted group permissions are not inherited")


def test_direct_and_group_permissions_combined():
    """User should see both direct and group-inherited permissions."""
    conn = create_test_db()
    cursor = conn.cursor()

    # Direct permission
    cursor.execute(
        "INSERT INTO user_permissions (user_id, resource_type, resource_id, permission) "
        "VALUES (100, 'network', NULL, 'view')"
    )

    # Group permission
    cursor.execute(
        "INSERT INTO groups (id, name, created_at) VALUES (1, 'VM Operators', '2024-01-01')"
    )
    cursor.execute(
        "INSERT INTO group_permissions (group_id, resource_type, resource_id, permission) "
        "VALUES (1, 'vm', NULL, 'view')"
    )
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, created_at) "
        "VALUES (1, 100, '2024-01-01')"
    )
    conn.commit()

    result = cursor.execute(
        "SELECT * FROM effective_user_permissions WHERE user_id = 100"
    ).fetchall()

    assert len(result) == 2, f"Expected 2 permissions (1 direct + 1 group), got {len(result)}"
    sources = {r["source"] for r in result}
    assert sources == {"direct", "group"}, f"Expected direct and group sources, got {sources}"
    print("PASS: Direct and group permissions are combined")


def test_removed_member_loses_group_permissions():
    """User should NOT inherit permissions after being removed from the group."""
    conn = create_test_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO groups (id, name, created_at) VALUES (1, 'VM Operators', '2024-01-01')"
    )
    cursor.execute(
        "INSERT INTO group_permissions (group_id, resource_type, resource_id, permission) "
        "VALUES (1, 'vm', NULL, 'view')"
    )
    # Member is soft-deleted (removed from group)
    cursor.execute(
        "INSERT INTO group_members (group_id, user_id, created_at, deleted_at) "
        "VALUES (1, 100, '2024-01-01', '2024-06-01')"
    )
    conn.commit()

    result = cursor.execute(
        "SELECT * FROM effective_user_permissions WHERE user_id = 100"
    ).fetchall()

    assert len(result) == 0, f"Expected 0 permissions for removed member, got {len(result)}"
    print("PASS: Removed member does not inherit group permissions")


if __name__ == "__main__":
    test_user_inherits_group_permissions()
    test_user_inherits_create_permission()
    test_deleted_group_permissions_not_inherited()
    test_direct_and_group_permissions_combined()
    test_removed_member_loses_group_permissions()
    print("\nAll permission inheritance tests passed!")
