"""
Permission Service - Fix for group permission inheritance.

Issue: Users assigned to groups do not inherit the permissions defined at the
group level. When a user logs in, they see no VMs and cannot create new VMs,
even though their group has the appropriate permissions.

Root Cause: The authorization check only evaluates direct user permissions and
does not resolve permissions inherited through group membership.

Fix: The permission check now queries both direct user permissions and
group-inherited permissions via the effective_user_permissions view (see
migration 001). The service layer below provides the application-level logic.
"""

from typing import Optional


class PermissionService:
    """Handles permission checks with group inheritance support."""

    def __init__(self, db):
        self.db = db

    def check_permission(
        self,
        user_id: int,
        resource_type: str,
        resource_id: Optional[int],
        permission: str,
    ) -> bool:
        """
        Check if a user has a specific permission on a resource.

        Evaluates both direct user permissions and permissions inherited
        through group membership.

        Args:
            user_id: The ID of the user to check.
            resource_type: The type of resource (e.g., 'vm', 'network').
            resource_id: The specific resource ID, or None for type-level perms.
            permission: The permission to check (e.g., 'view', 'create', 'edit').

        Returns:
            True if the user has the permission, False otherwise.
        """
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM effective_user_permissions eup
                WHERE eup.user_id = %s
                  AND eup.resource_type = %s
                  AND (eup.resource_id = %s OR eup.resource_id IS NULL)
                  AND eup.permission = %s
            )
        """
        result = self.db.execute(query, (user_id, resource_type, resource_id, permission))
        return result.scalar()

    def get_user_permissions(self, user_id: int) -> list[dict]:
        """
        Get all effective permissions for a user, including group-inherited ones.

        Args:
            user_id: The ID of the user.

        Returns:
            List of permission dicts with source information.
        """
        query = """
            SELECT resource_type, resource_id, permission, source, source_group_id
            FROM effective_user_permissions
            WHERE user_id = %s
            ORDER BY resource_type, permission
        """
        rows = self.db.execute(query, (user_id,)).fetchall()
        return [
            {
                "resource_type": row.resource_type,
                "resource_id": row.resource_id,
                "permission": row.permission,
                "source": row.source,
                "source_group_id": row.source_group_id,
            }
            for row in rows
        ]

    def get_accessible_resources(self, user_id: int, resource_type: str) -> list[int]:
        """
        Get all resource IDs of a given type that a user can access.

        This resolves the reported issue where users could not see any VMs
        after being added to a group with VM view permissions.

        Args:
            user_id: The ID of the user.
            resource_type: The resource type to query (e.g., 'vm').

        Returns:
            List of accessible resource IDs.
        """
        query = """
            SELECT DISTINCT resource_id
            FROM effective_user_permissions
            WHERE user_id = %s
              AND resource_type = %s
              AND permission IN ('view', 'admin')
              AND resource_id IS NOT NULL
        """
        rows = self.db.execute(query, (user_id, resource_type)).fetchall()
        return [row.resource_id for row in rows]

    def user_can_create(self, user_id: int, resource_type: str) -> bool:
        """
        Check if a user can create resources of a given type.

        This resolves the reported issue where users could not create new VMs
        even though their group had create permissions.

        Args:
            user_id: The ID of the user.
            resource_type: The resource type to check (e.g., 'vm').

        Returns:
            True if the user has create permission (directly or via group).
        """
        return self.check_permission(user_id, resource_type, None, "create")
