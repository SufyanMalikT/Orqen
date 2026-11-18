
from rest_framework.permissions import BasePermission
from .models import WorkspaceMembership

class IsWorkspaceMember(BasePermission):
    message = "Only workspace members can do perform this operation"
    def has_permissions(self, request, view):

        workspace_id = self.kwargs['workspace_id']
        
        return WorkspaceMembership.objects.filter(
            workspace__id = workspace_id,
            user=request.user
        ).exists()
class IsWorkspaceOwnerOrAdmin(BasePermission):
    message = "Only workspace owners and admins can manage memberships."

    allowed_roles = ["OWNER", "ADMIN"]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        workspace_id = view.kwargs['workspace_id']

        return WorkspaceMembership.objects.filter(
            user=request.user,
            workspace_id=workspace_id,
            role__in=self.allowed_roles
        ).exists()


class IsWorkspaceOwner(IsWorkspaceOwnerOrAdmin):
    message = "Only workspace owners can perform this operation."

    allowed_roles = ["OWNER"]


class CanManageTargetMembership(IsWorkspaceOwnerOrAdmin):
    message = "You cannot manage this membership."

    def has_object_permission(self, request, view, obj):

        requester_role = WorkspaceMembership.objects.filter(
            workspace=obj.workspace,
            user=request.user
        ).values_list("role", flat=True).first()

        # Only OWNER can change membership roles.
        if request.method in ["PUT", "PATCH"]:
            return requester_role == "OWNER"

        # Nobody can delete the OWNER.
        if request.method == "DELETE":
            if obj.role == "OWNER":
                return False

            # ADMIN can only delete ordinary members.
            if requester_role == "ADMIN":
                return obj.role == "MEMBER"

        return True
