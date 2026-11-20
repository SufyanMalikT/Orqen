from rest_framework import serializers
from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from .models import Project, Workspace, WorkspaceMembership
from .services import create_workspace


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = WorkspaceMembership
        fields = ["id", "role", "workspace", "user", "created_at", "updated_at"]
        read_only_fields = ["id", "role", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        workspace = self.context.get("workspace")
        user = attrs.get("user")

        if workspace:
            if workspace.kind == Workspace.Kind.PERSONAL:
                raise serializers.ValidationError("Personal workspaces cannot have additional members.")

            if WorkspaceMembership.objects.filter(workspace=workspace, user=user).exists():
                raise serializers.ValidationError({"user": "This user is already a member of this workspace."})

        return attrs

    def create(self, validated_data):
        workspace = self.context.get("workspace") or validated_data.get("workspace")
        validated_data["workspace"] = workspace
        validated_data["role"] = WorkspaceMembership.Role.MEMBER
        return WorkspaceMembership.objects.create(**validated_data)


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    memberships = WorkspaceMembershipSerializer(read_only=True, many=True)

    class Meta:
        model = Workspace
        fields = ["id", "name", "kind", "created_by", "memberships", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_kind(self, value):
        workspace = self.instance
        if workspace and workspace.kind == Workspace.Kind.TEAM and value == Workspace.Kind.PERSONAL:
            raise serializers.ValidationError("Team workspaces cannot be converted to personal workspaces.")
        return value

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", Workspace.Kind.PERSONAL))
        request = self.context.get("request")
        user = request.user if request else None

        if self.instance is None and user and kind == Workspace.Kind.PERSONAL:
            if Workspace.objects.filter(created_by=user, kind=Workspace.Kind.PERSONAL).exists():
                raise serializers.ValidationError({"kind": "A user can have only one personal workspace."})

        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        return create_workspace(user, validated_data)


class WorkspaceMembershipUpdateRoleSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=WorkspaceMembership.Role.choices)

    class Meta:
        model = WorkspaceMembership
        fields = ["role"]

    def validate_role(self, value):
        if value == WorkspaceMembership.Role.OWNER:
            raise serializers.ValidationError("Ownership transfer must not happen through ordinary role updates.")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.role == WorkspaceMembership.Role.OWNER:
            raise serializers.ValidationError("Cannot change the owner's role.")
        return attrs


class ProjectSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "workspace", "name", "description", "is_archived", "created_at", "updated_at"]
        read_only_fields = ["id", "workspace", "created_at", "updated_at"]

    def validate(self, attrs):
        workspace = self.context.get("workspace")
        if not workspace and self.instance:
            workspace = self.instance.workspace

        name = attrs.get("name", getattr(self.instance, "name", None))
        if workspace and name:
            query = Project.objects.filter(workspace=workspace, name=name)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError({"name": "A project with this name already exists in this workspace."})

        return attrs
