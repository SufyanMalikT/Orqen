from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from .models import Workspace, WorkspaceMembership


def get_workspace_or_404(workspace_id):
    """Retrieve workspace by ID or raise DRF NotFound (HTTP 404)."""
    try:
        return Workspace.objects.get(pk=workspace_id)
    except (Workspace.DoesNotExist, ValueError):
        raise NotFound(detail="Workspace not found.")


class IsWorkspaceMember(BasePermission):
    message = "Only workspace members can perform this operation."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs.get("workspace_id")
        if not workspace_id:
            return False

        # Ensure workspace exists (returns 404 if not found)
        get_workspace_or_404(workspace_id)

        return WorkspaceMembership.objects.filter(
            workspace_id=workspace_id,
            user=request.user
        ).exists()

    def has_object_permission(self, request, view, obj):
        workspace = getattr(obj, "workspace", obj)
        return WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=request.user
        ).exists()


class IsWorkspaceOwnerOrAdmin(BasePermission):
    message = "Only workspace owners and admins can perform this operation."
    allowed_roles = [WorkspaceMembership.Role.OWNER, WorkspaceMembership.Role.ADMIN]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs.get("workspace_id")
        if not workspace_id:
            return False

        # Ensure workspace exists (returns 404 if not found)
        get_workspace_or_404(workspace_id)

        return WorkspaceMembership.objects.filter(
            user=request.user,
            workspace_id=workspace_id,
            role__in=self.allowed_roles
        ).exists()

    def has_object_permission(self, request, view, obj):
        workspace = getattr(obj, "workspace", obj)
        return WorkspaceMembership.objects.filter(
            user=request.user,
            workspace=workspace,
            role__in=self.allowed_roles
        ).exists()


class IsWorkspaceOwner(IsWorkspaceOwnerOrAdmin):
    message = "Only workspace owners can perform this operation."
    allowed_roles = [WorkspaceMembership.Role.OWNER]


class CanManageTargetMembership(IsWorkspaceOwnerOrAdmin):
    message = "You cannot manage this membership."

    def has_object_permission(self, request, view, obj):
        workspace_id = view.kwargs.get("workspace_id")
        if workspace_id and str(obj.workspace_id) != str(workspace_id):
            return False

        requester_membership = WorkspaceMembership.objects.filter(
            workspace=obj.workspace,
            user=request.user
        ).first()

        if not requester_membership:
            return False

        requester_role = requester_membership.role

        # Only OWNER can change membership roles.
        if request.method in ["PUT", "PATCH"]:
            if requester_role != WorkspaceMembership.Role.OWNER:
                return False
            # Owner cannot change their own role through this endpoint.
            if obj.role == WorkspaceMembership.Role.OWNER:
                return False
            return True

        # Deletion rules:
        if request.method == "DELETE":
            # Nobody can delete the OWNER (including the OWNER).
            if obj.role == WorkspaceMembership.Role.OWNER:
                return False

            # OWNER can remove admins and members.
            if requester_role == WorkspaceMembership.Role.OWNER:
                return True

            # ADMIN can only remove ordinary members.
            if requester_role == WorkspaceMembership.Role.ADMIN:
                return obj.role == WorkspaceMembership.Role.MEMBER

            return False

        return True
