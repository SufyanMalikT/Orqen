from rest_framework import serializers
from .models import TimeStampedModel, Workspace, WorkspaceMembership, Project
from apps.accounts.serializers import UserSerializer
from .services import create_workspace
from apps.accounts.models import User


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
        )
    
    class Meta:
        model = WorkspaceMembership
        fields = ['id','role','workspace','user','created_at','updated_at']
        read_only_fields = ['id','role','workspace']

    def create(self, validated_data):
        workspace = validated_data.get('workspace')
        user = validated_data.get('user')
        role = validated_data.get('role')

        # enforcing only one and only owner membership on personal workspaces 
        if workspace.kind == Workspace.Kind.PERSONAL:
            if (
                user != workspace.created_by
                or role != WorkspaceMembership.Role.OWNER
            ):
                raise serializers.ValidationError("Personal workspace cannot have additional mmebers")
        return WorkspaceMembership.objects.create(**validated_data)


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    memberships = WorkspaceMembershipSerializer(read_only=True, many=True)
    class Meta:
        model = Workspace
        fields = '__all__'
        read_only_fields = ['id']

    def validate_kind(self,value):
        workspace = self.instance
        if (
            workspace 
            and value == Workspace.Kind.PERSONAL
            and workspace.kind == 'TEAM'
        ):
            raise serializers.ValidationError("Team workspaces cannot be converted to personal workspaces.")

        return value

    def create(self, validated_data):
        user = self.context['request'].user
        return create_workspace(user, validated_data)

class WorkspaceMembershipUpdateRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceMembership
        fields = ['role']

class ProjectSerializer(serializers.ModelSerializer):
    workspace = WorkspaceSerializer(read_only=True)
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id']


