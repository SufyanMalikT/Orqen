from django.urls import path
from .views import WorkspaceListCreateAPIView, WorkspaceRetrieveUpdateDestroyAPIView, \
    WorkspaceMembershipListCreateAPIView, WorkspaceMembershipRetrieveUpdateDestroyAPIView, \
        ProjectListCreateAPIView, ProjectRetrieveUpdateDestroyAPIView
urlpatterns = [
    path('',WorkspaceListCreateAPIView.as_view(), name='create_workspace'),
    path('<uuid:workspace_id>/',WorkspaceRetrieveUpdateDestroyAPIView.as_view(),name='retrieve_update_destroy_workspaces'),
    path('<uuid:workspace_id>/memberships/',WorkspaceMembershipListCreateAPIView.as_view(), name='list_create_memberships' ),
    path('<uuid:workspace_id>/memberships/<uuid:membership_id>/',WorkspaceMembershipRetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_delete_memberships'),
    path('<uuid:workspace_id>/projects/', ProjectListCreateAPIView.as_view(), name='list_create_projects'),
    path('<uuid:workspace_id>/projects/<uuid:project_id>/',ProjectRetrieveUpdateDestroyAPIView.as_view(), name='retrieve_update_destroy_projects')
]