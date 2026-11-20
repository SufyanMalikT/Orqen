from django.db import transaction
from .models import Workspace, WorkspaceMembership
@transaction.atomic
def create_workspace(user, validated_data):
    workspace = Workspace.objects.create(
        created_by=user,
        **validated_data
    )

    WorkspaceMembership.objects.create(
        user=user,
        role='OWNER',
        workspace=workspace
    )

    return workspace