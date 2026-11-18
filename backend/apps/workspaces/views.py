from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Workspace, WorkspaceMembership, Project
from .serializers import WorkspaceSerializer, WorkspaceMembershipSerializer, \
    WorkspaceMembershipUpdateRoleSerializer, ProjectSerializer
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from .permissions import IsWorkspaceMember, IsWorkspaceOwner, IsWorkspaceOwnerOrAdmin, CanManageTargetMembership
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from apps.accounts.models import User
# Create your views here.

class WorkspaceListCreateAPIView(ListCreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Workspace.objects.filter(
            memberships__user=self.request.user
        )
class WorkspaceRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceSerializer
    lookup_url_kwarg = 'workspace_id'

    def get_queryset(self):
        return Workspace.objects.filter(
            memberships__user=self.request.user,
            pk=self.kwargs['workspace_id']
        ).distinct()

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated, IsWorkspaceMember]
        else:
            permission_classes = [IsAuthenticated, IsWorkspaceOwner]

        return [permission() for permission in permission_classes]


class WorkspaceMembershipListCreateAPIView(ListCreateAPIView):
    serializer_class = WorkspaceMembershipSerializer

    def perform_create(self, serializer):
        workspace = get_object_or_404(
            Workspace,
            pk=self.kwargs['workspace_id']
        )
        user_id = self.request.data.get('user')
        user = get_object_or_404(User, pk=user_id)
        serializer.save(
            workspace=workspace,
            user=user,
            role='MEMBER'
        )

    def get_queryset(self):
        return WorkspaceMembership.objects.filter(
            workspace__id=self.kwargs['workspace_id'],
            workspace__memberships__user=self.request.user
        ).distinct()

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsWorkspaceOwnerOrAdmin]

        return [permission() for permission in permission_classes]

    
class WorkspaceMembershipRetrieveUpdateDestroyAPIView(
    RetrieveUpdateDestroyAPIView
):
    serializer_class = WorkspaceMembershipSerializer
    lookup_url_kwarg = 'membership_id'
    def get_queryset(self):
        return WorkspaceMembership.objects.filter(
            pk=self.kwargs['membership_id'],
        ).distinct()

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [
                IsAuthenticated,
                CanManageTargetMembership
            ]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return WorkspaceMembershipUpdateRoleSerializer

        return self.serializer_class


class ProjectListCreateAPIView(ListCreateAPIView):
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        name = self.request.data.get('name')
        workspace = get_object_or_404(Workspace, pk=self.kwargs['workspace_id'])
        serializer.save( name=name, workspace=workspace)

    def get_queryset(self):
        return Project.objects.filter(
            workspace__id=self.kwargs['workspace_id']
        )

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsWorkspaceOwnerOrAdmin]
        
        return [permission() for permission in permission_classes]

class ProjectRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    lookup_url_kwarg = 'project_id'

    def get_queryset(self):
        return Project.objects.filter(
            id=self.kwargs['project_id'],
        )

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsWorkspaceOwnerOrAdmin]
        
        return [permission() for permission in permission_classes]

    