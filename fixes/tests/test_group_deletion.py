"""
Tests for group deletion and name reuse fix.

Verifies that after soft-deleting a group, a new group can be created with
the same name.
"""

import sqlite3


def create_test_db():
    """Create an in-memory SQLite database with the required schema and fix."""
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

        -- The fix: partial unique index only on active groups.
        -- In SQLite, we use a filtered index (WHERE deleted_at IS NULL).
        CREATE UNIQUE INDEX idx_groups_name_unique_active
            ON groups (name)
            WHERE deleted_at IS NULL;
    """)

    conn.commit()
    return conn


def test_cannot_create_duplicate_active_groups():
    """Two active groups with the same name should not be allowed."""
    conn = create_test_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO groups (name, created_at) VALUES ('QTDC', '2024-01-01')"
    )
    conn.commit()

    try:
        cursor.execute(
            "INSERT INTO groups (name, created_at) VALUES ('QTDC', '2024-06-01')"
        )
        conn.commit()
        assert False, "Should have raised an IntegrityError for duplicate active group names"
    except sqlite3.IntegrityError:
        print("PASS: Cannot create duplicate active group names")


def test_can_reuse_deleted_group_name():
    """After soft-deleting a group, a new group with the same name should be allowed."""
    conn = create_test_db()
    cursor = conn.cursor()

    # Create and soft-delete a group named 'QTDC'
    cursor.execute(
        "INSERT INTO groups (name, created_at) VALUES ('QTDC', '2024-01-01')"
    )
    cursor.execute(
        "UPDATE groups SET deleted_at = '2024-06-01' WHERE name = 'QTDC'"
    )
    conn.commit()

    # Now create a new group with the same name - this should succeed
    try:
        cursor.execute(
            "INSERT INTO groups (name, created_at) VALUES ('QTDC', '2024-07-01')"
        )
        conn.commit()
        print("PASS: Can reuse deleted group name")
    except sqlite3.IntegrityError:
        assert False, "Should be able to reuse a deleted group's name"


def test_multiple_deleted_groups_same_name():
    """Multiple soft-deleted groups can share the same name."""
    conn = create_test_db()
    cursor = conn.cursor()

    # Create and delete 'QTDC' multiple times
    for i in range(3):
        cursor.execute(
            "INSERT INTO groups (name, created_at) VALUES ('QTDC', ?)",
            (f"2024-0{i+1}-01",),
        )
        cursor.execute(
            "UPDATE groups SET deleted_at = ? WHERE name = 'QTDC' AND deleted_at IS NULL",
            (f"2024-0{i+1}-15",),
        )
    conn.commit()

    # Create a new active group with the same name
    cursor.execute(
        "INSERT INTO groups (name, created_at) VALUES ('QTDC', '2024-07-01')"
    )
    conn.commit()

    # Verify: 3 deleted + 1 active
    all_groups = cursor.execute("SELECT * FROM groups WHERE name = 'QTDC'").fetchall()
    active = [g for g in all_groups if g["deleted_at"] is None]
    deleted = [g for g in all_groups if g["deleted_at"] is not None]

    assert len(active) == 1, f"Expected 1 active group, got {len(active)}"
    assert len(deleted) == 3, f"Expected 3 deleted groups, got {len(deleted)}"
    print("PASS: Multiple deleted groups can share the same name with one active")


def test_delete_and_recreate_preserves_history():
    """Soft-deleting and recreating preserves the old group record."""
    conn = create_test_db()
    cursor = conn.cursor()

    # Create original group
    cursor.execute(
        "INSERT INTO groups (name, description, created_at) "
        "VALUES ('QTDC', 'Original', '2024-01-01')"
    )
    original_id = cursor.lastrowid

    # Soft-delete it
    cursor.execute(
        "UPDATE groups SET deleted_at = '2024-06-01' WHERE id = ?",
        (original_id,),
    )

    # Create new group with same name
    cursor.execute(
        "INSERT INTO groups (name, description, created_at) "
        "VALUES ('QTDC', 'New version', '2024-07-01')"
    )
    new_id = cursor.lastrowid
    conn.commit()

    # Both records exist
    original = cursor.execute(
        "SELECT * FROM groups WHERE id = ?", (original_id,)
    ).fetchone()
    new = cursor.execute("SELECT * FROM groups WHERE id = ?", (new_id,)).fetchone()

    assert original is not None, "Original group record should still exist"
    assert original["deleted_at"] is not None, "Original should be soft-deleted"
    assert new["deleted_at"] is None, "New group should be active"
    assert original["description"] == "Original"
    assert new["description"] == "New version"
    print("PASS: Soft-delete and recreate preserves history")


if __name__ == "__main__":
    test_cannot_create_duplicate_active_groups()
    test_can_reuse_deleted_group_name()
    test_multiple_deleted_groups_same_name()
    test_delete_and_recreate_preserves_history()
    print("\nAll group deletion tests passed!")
