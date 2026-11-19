from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS

from .models import Project, Workspace, WorkspaceMembership
from .permissions import (
    CanManageTargetMembership,
    IsWorkspaceMember,
    IsWorkspaceOwner,
    IsWorkspaceOwnerOrAdmin,
)
from .serializers import (
    ProjectSerializer,
    WorkspaceMembershipSerializer,
    WorkspaceMembershipUpdateRoleSerializer,
    WorkspaceSerializer,
)


class WorkspaceListCreateAPIView(ListCreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Workspace.objects.filter(memberships__user=self.request.user)
            .distinct()
            .order_by("-created_at")
        )


class WorkspaceRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceSerializer
    lookup_url_kwarg = "workspace_id"

    def get_queryset(self):
        return (
            Workspace.objects.filter(
                memberships__user=self.request.user,
                pk=self.kwargs["workspace_id"],
            )
            .distinct()
        )

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated, IsWorkspaceMember]
        else:
            permission_classes = [IsAuthenticated, IsWorkspaceOwner]

        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        with transaction.atomic():
            instance.projects.all().delete()
            instance.delete()


class WorkspaceMembershipListCreateAPIView(ListCreateAPIView):
    serializer_class = WorkspaceMembershipSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = get_object_or_404(Workspace, pk=self.kwargs["workspace_id"])
        return context

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated, IsWorkspaceMember]
        else:
            permission_classes = [IsAuthenticated, IsWorkspaceOwnerOrAdmin]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return (
            WorkspaceMembership.objects.filter(workspace_id=self.kwargs["workspace_id"])
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        workspace = get_object_or_404(Workspace, pk=self.kwargs["workspace_id"])
        serializer.save(
            workspace=workspace,
            role=WorkspaceMembership.Role.MEMBER,
        )


class WorkspaceMembershipRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceMembershipSerializer
    lookup_url_kwarg = "membership_id"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = get_object_or_404(Workspace, pk=self.kwargs["workspace_id"])
        return context

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated, IsWorkspaceMember]
        else:
            permission_classes = [IsAuthenticated, CanManageTargetMembership]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return WorkspaceMembershipUpdateRoleSerializer
        return self.serializer_class

    def get_queryset(self):
        return WorkspaceMembership.objects.filter(
            workspace_id=self.kwargs["workspace_id"],
            pk=self.kwargs["membership_id"],
        ).distinct()


class ProjectListCreateAPIView(ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = get_object_or_404(Workspace, pk=self.kwargs["workspace_id"])
        return context

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated, IsWorkspaceMember]
        else:
            permission_classes = [IsAuthenticated, IsWorkspaceOwnerOrAdmin]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return (
            Project.objects.filter(workspace_id=self.kwargs["workspace_id"])
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        workspace = get_object_or_404(Workspace, pk=self.kwargs["workspace_id"])
        serializer.save(workspace=workspace)


class ProjectRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    lookup_url_kwarg = "project_id"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["workspace"] = get_object_or_404(Workspace, pk=self.kwargs["workspace_id"])
        return context

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated, IsWorkspaceMember]
        else:
            permission_classes = [IsAuthenticated, IsWorkspaceOwnerOrAdmin]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return Project.objects.filter(
            workspace_id=self.kwargs["workspace_id"],
            pk=self.kwargs["project_id"],
        ).distinct()
