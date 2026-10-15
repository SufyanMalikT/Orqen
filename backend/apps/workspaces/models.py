import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Workspace(TimeStampedModel):
    class Kind(models.TextChoices):
        PERSONAL = "PERSONAL", "Personal"
        TEAM = "TEAM", "Team"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(max_length=100)
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.PERSONAL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_workspaces",
    )

    class Meta:
        constraints = [
            # One personal workspace per creator.
            models.UniqueConstraint(
                fields=["created_by"],
                condition=Q(kind="PERSONAL"),
                name="unique_personal_workspace_per_creator",
            ),
        ]

    def __str__(self):
        return self.name


class WorkspaceMembership(TimeStampedModel):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        MEMBER = "MEMBER", "Member"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspace_memberships",
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"],
                name="unique_user_per_workspace",
            ),
            # A workspace may have at most one OWNER membership.
            models.UniqueConstraint(
                fields=["workspace"],
                condition=Q(role="OWNER"),
                name="unique_workspace_owner",
            ),
        ]


class Project(TimeStampedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name"],
                name="unique_project_name_per_workspace",
            ),
        ]

    def __str__(self):
        return self.name