"""
Group Service - Fix for group deletion and name reuse.

Issue: After deleting a group, creating a new group with the same name fails.
The system reports the group name already exists, even though it was deleted.

Root Cause: The group deletion uses soft delete (sets deleted_at timestamp),
but the unique constraint on the group name column does not exclude
soft-deleted records. The uniqueness check also queries all groups regardless
of deletion status.

Fix:
1. Database: Replace the unique constraint with a partial unique index that
   only enforces uniqueness among active (non-deleted) groups (see migration
   002).
2. Application: Update the name uniqueness validation to exclude soft-deleted
   groups.
"""

from datetime import datetime, timezone
from typing import Optional


class GroupService:
    """Handles group CRUD operations with proper soft-delete support."""

    def __init__(self, db):
        self.db = db

    def create_group(self, name: str, description: str = "") -> dict:
        """
        Create a new group.

        The uniqueness check only considers active (non-deleted) groups,
        allowing reuse of names from previously deleted groups.

        Args:
            name: The group name.
            description: Optional group description.

        Returns:
            The created group record.

        Raises:
            ValueError: If an active group with the same name already exists.
        """
        # Only check against active (non-deleted) groups
        existing = self.db.execute(
            "SELECT id FROM groups WHERE name = %s AND deleted_at IS NULL",
            (name,),
        ).fetchone()

        if existing:
            raise ValueError(f"An active group with name '{name}' already exists.")

        result = self.db.execute(
            """
            INSERT INTO groups (name, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, description, created_at
            """,
            (name, description, datetime.now(timezone.utc), datetime.now(timezone.utc)),
        ).fetchone()

        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "created_at": result.created_at,
        }

    def delete_group(self, group_id: int) -> bool:
        """
        Soft-delete a group by setting deleted_at.

        After this migration fix, the group's name becomes available for reuse
        because the partial unique index only enforces uniqueness among active
        groups.

        Args:
            group_id: The ID of the group to delete.

        Returns:
            True if the group was deleted, False if not found.
        """
        now = datetime.now(timezone.utc)
        result = self.db.execute(
            """
            UPDATE groups
            SET deleted_at = %s, updated_at = %s
            WHERE id = %s AND deleted_at IS NULL
            """,
            (now, now, group_id),
        )
        return result.rowcount > 0

    def hard_delete_group(self, group_id: int) -> bool:
        """
        Permanently delete a group and all associated records.

        Use this as an alternative to soft-delete when the group and its
        history should be completely removed.

        Args:
            group_id: The ID of the group to permanently delete.

        Returns:
            True if the group was deleted, False if not found.
        """
        # Remove group memberships
        self.db.execute(
            "DELETE FROM group_members WHERE group_id = %s",
            (group_id,),
        )

        # Remove group permissions
        self.db.execute(
            "DELETE FROM group_permissions WHERE group_id = %s",
            (group_id,),
        )

        # Remove the group
        result = self.db.execute(
            "DELETE FROM groups WHERE id = %s",
            (group_id,),
        )
        return result.rowcount > 0

    def add_member(self, group_id: int, user_id: int) -> bool:
        """
        Add a user to a group.

        After the permission inheritance fix, the user will immediately
        inherit all permissions assigned to the group.

        Args:
            group_id: The group to add the user to.
            user_id: The user to add.

        Returns:
            True if the member was added, False if already a member.
        """
        existing = self.db.execute(
            """
            SELECT id FROM group_members
            WHERE group_id = %s AND user_id = %s AND deleted_at IS NULL
            """,
            (group_id, user_id),
        ).fetchone()

        if existing:
            return False

        self.db.execute(
            """
            INSERT INTO group_members (group_id, user_id, created_at)
            VALUES (%s, %s, %s)
            """,
            (group_id, user_id, datetime.now(timezone.utc)),
        )
        return True

    def get_group(self, group_id: int) -> Optional[dict]:
        """
        Get a group by ID (active groups only).

        Args:
            group_id: The group ID.

        Returns:
            The group record or None if not found/deleted.
        """
        result = self.db.execute(
            """
            SELECT id, name, description, created_at
            FROM groups
            WHERE id = %s AND deleted_at IS NULL
            """,
            (group_id,),
        ).fetchone()

        if not result:
            return None

        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "created_at": result.created_at,
        }
