import uuid
from django.db import models
from ..accounts.models import User
from ..workspaces.models import Project, TimeStampedModel
# Create your models here.


class Collection(TimeStampedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.PROTECT,
        related_name="collections",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"],
                name="unique_collection_name_per_project",
            ),
        ]

    def __str__(self):
        return self.name


class SavedRequest(TimeStampedModel):
    class Method(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"
        OPTIONS = "OPTIONS", "OPTIONS"
        HEAD = "HEAD", "HEAD"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.PROTECT,
        related_name="requests",
    )
    name = models.CharField(max_length=120)
    method = models.CharField(
        max_length=10,
        choices=Method.choices,
        default=Method.GET,
    )
    url = models.URLField(max_length=2048)
    query_params = models.JSONField(default=dict, blank=True)
    headers = models.JSONField(default=dict, blank=True)
    body = models.JSONField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]

    def __str__(self):
        return f"{self.method} {self.name}"


class RequestExecution(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    saved_request = models.ForeignKey(
        SavedRequest,
        on_delete=models.PROTECT,
        related_name="executions",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    http_status_code = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )
    response_body = models.TextField(blank=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)