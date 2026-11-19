import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMembership, Project
from apps.workspaces.services import create_workspace


class BaseWorkspaceAPITestCase(APITestCase):
    """Base setup providing users and workspaces with different roles."""

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="Password123!",
            first_name="Owner",
            last_name="User"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="Password123!",
            first_name="Admin",
            last_name="User"
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="Password123!",
            first_name="Member",
            last_name="User"
        )
        self.outsider = User.objects.create_user(
            email="outsider@example.com",
            password="Password123!",
            first_name="Outsider",
            last_name="User"
        )

        # Team workspace with owner, admin, and member
        self.team_workspace = create_workspace(
            self.owner,
            {"name": "Alpha Team", "kind": Workspace.Kind.TEAM}
        )
        self.admin_membership = WorkspaceMembership.objects.create(
            workspace=self.team_workspace,
            user=self.admin,
            role=WorkspaceMembership.Role.ADMIN
        )
        self.member_membership = WorkspaceMembership.objects.create(
            workspace=self.team_workspace,
            user=self.member,
            role=WorkspaceMembership.Role.MEMBER
        )
        self.owner_membership = self.team_workspace.memberships.get(user=self.owner)

        # Workspace 2 owned by outsider
        self.other_workspace = create_workspace(
            self.outsider,
            {"name": "Beta Team", "kind": Workspace.Kind.TEAM}
        )
        self.other_owner_membership = self.other_workspace.memberships.get(user=self.outsider)

    def get_results(self, response_data):
        """Helper to unpack paginated or non-paginated list responses."""
        if isinstance(response_data, dict) and "results" in response_data:
            return response_data["results"]
        return response_data


class WorkspaceLifecycleTests(BaseWorkspaceAPITestCase):
    """Tests covering Workspace CRUD, rules, and lifecycle transitions."""

    def test_unauthenticated_requests_rejected(self):
        """Unauthenticated requests to workspaces endpoints must be rejected with 401."""
        response = self.client.get("/api/v1/workspaces/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post("/api/v1/workspaces/", {"name": "New WS"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.get(f"/api/v1/workspaces/{self.team_workspace.id}/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_workspace_creation_and_automatic_owner_membership(self):
        """Creating a workspace succeeds and automatically grants OWNER membership."""
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            "/api/v1/workspaces/",
            {"name": "Gamma Team", "kind": Workspace.Kind.TEAM},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        workspace_id = response.data["id"]

        workspace = Workspace.objects.get(id=workspace_id)
        self.assertEqual(workspace.name, "Gamma Team")
        self.assertEqual(workspace.kind, Workspace.Kind.TEAM)
        self.assertEqual(workspace.created_by, self.member)

        # Check membership
        membership = WorkspaceMembership.objects.get(workspace=workspace, user=self.member)
        self.assertEqual(membership.role, WorkspaceMembership.Role.OWNER)

    def test_personal_workspace_uniqueness(self):
        """A user can have only one personal workspace. Second creation must return 400."""
        self.client.force_authenticate(user=self.outsider)
        # Create first personal workspace
        resp1 = self.client.post(
            "/api/v1/workspaces/",
            {"name": "Personal 1", "kind": Workspace.Kind.PERSONAL},
            format="json"
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Attempt to create second personal workspace
        resp2 = self.client.post(
            "/api/v1/workspaces/",
            {"name": "Personal 2", "kind": Workspace.Kind.PERSONAL},
            format="json"
        )
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_personal_workspace_membership_restrictions(self):
        """Adding any additional member to a personal workspace must be rejected."""
        personal_ws = create_workspace(
            self.owner,
            {"name": "Owner Personal", "kind": Workspace.Kind.PERSONAL}
        )
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/v1/workspaces/{personal_ws.id}/memberships/",
            {"user": str(self.member.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_personal_to_team_conversion_allowed_for_owner(self):
        """Owner can convert a PERSONAL workspace to a TEAM workspace."""
        personal_ws = create_workspace(
            self.owner,
            {"name": "Owner Personal", "kind": Workspace.Kind.PERSONAL}
        )
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/v1/workspaces/{personal_ws.id}/",
            {"kind": Workspace.Kind.TEAM},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        personal_ws.refresh_from_db()
        self.assertEqual(personal_ws.kind, Workspace.Kind.TEAM)

    def test_team_to_personal_conversion_rejected(self):
        """Converting a TEAM workspace back into a PERSONAL workspace must be rejected with 400."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/",
            {"kind": Workspace.Kind.PERSONAL},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.team_workspace.refresh_from_db()
        self.assertEqual(self.team_workspace.kind, Workspace.Kind.TEAM)

    def test_owner_can_update_workspace_name(self):
        """Owner can update workspace name."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/",
            {"name": "Updated Alpha Team"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.team_workspace.refresh_from_db()
        self.assertEqual(self.team_workspace.name, "Updated Alpha Team")

    def test_admin_and_member_cannot_update_workspace_settings(self):
        """Admin and Member cannot update workspace name or settings."""
        self.client.force_authenticate(user=self.admin)
        resp_admin = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/",
            {"name": "Admin Hacked Name"},
            format="json"
        )
        self.assertEqual(resp_admin.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.member)
        resp_member = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/",
            {"name": "Member Hacked Name"},
            format="json"
        )
        self.assertEqual(resp_member.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_owner_can_delete_workspace(self):
        """Admin and Member cannot delete workspace; only Owner can delete it."""
        self.client.force_authenticate(user=self.member)
        resp_member = self.client.delete(f"/api/v1/workspaces/{self.team_workspace.id}/")
        self.assertEqual(resp_member.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        resp_admin = self.client.delete(f"/api/v1/workspaces/{self.team_workspace.id}/")
        self.assertEqual(resp_admin.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.owner)
        resp_owner = self.client.delete(f"/api/v1/workspaces/{self.team_workspace.id}/")
        self.assertEqual(resp_owner.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workspace.objects.filter(id=self.team_workspace.id).exists())

    def test_workspace_listing_only_returns_user_workspaces(self):
        """Workspace listing returns only workspaces where the user has a membership."""
        self.client.force_authenticate(user=self.member)
        response = self.client.get("/api/v1/workspaces/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self.get_results(response.data)
        returned_ids = [w["id"] for w in results]
        self.assertIn(str(self.team_workspace.id), returned_ids)
        self.assertNotIn(str(self.other_workspace.id), returned_ids)


class WorkspaceMembershipTests(BaseWorkspaceAPITestCase):
    """Tests for workspace membership creation, role updates, and deletions."""

    def test_owner_and_admin_can_add_member(self):
        """Both OWNER and ADMIN can add ordinary members."""
        new_user_1 = User.objects.create_user(email="user1@example.com", password="Password123!")
        new_user_2 = User.objects.create_user(email="user2@example.com", password="Password123!")

        # Owner adds user1
        self.client.force_authenticate(user=self.owner)
        resp1 = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/",
            {"user": str(new_user_1.id)},
            format="json"
        )
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp1.data["role"], "MEMBER")

        # Admin adds user2
        self.client.force_authenticate(user=self.admin)
        resp2 = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/",
            {"user": str(new_user_2.id)},
            format="json"
        )
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.data["role"], "MEMBER")

    def test_member_cannot_add_members(self):
        """MEMBER cannot add new members."""
        new_user = User.objects.create_user(email="user_m@example.com", password="Password123!")
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/",
            {"user": str(new_user.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_cannot_assign_owner_or_admin_on_creation(self):
        """Supplying OWNER or ADMIN role at creation is overridden to MEMBER on backend."""
        new_user = User.objects.create_user(email="role_escalate@example.com", password="Password123!")
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/",
            {"user": str(new_user.id), "role": "OWNER"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "MEMBER")
        membership = WorkspaceMembership.objects.get(id=response.data["id"])
        self.assertEqual(membership.role, WorkspaceMembership.Role.MEMBER)

    def test_duplicate_memberships_rejected(self):
        """Adding a user who is already a member must return 400 Bad Request."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/",
            {"user": str(self.member.id)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_members_can_view_memberships_in_workspace(self):
        """All workspace members can view memberships of their workspace."""
        for user in [self.owner, self.admin, self.member]:
            self.client.force_authenticate(user=user)
            response = self.client.get(f"/api/v1/workspaces/{self.team_workspace.id}/memberships/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            results = self.get_results(response.data)
            self.assertEqual(len(results), 3)

    def test_users_cannot_view_memberships_from_another_workspace(self):
        """Users outside the workspace cannot view its memberships."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.get(f"/api/v1/workspaces/{self.team_workspace.id}/memberships/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_only_owner_can_change_roles(self):
        """Only OWNER can change membership roles; Admin and Member cannot."""
        # Admin attempts to promote member to ADMIN -> 403
        self.client.force_authenticate(user=self.admin)
        resp_admin = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.member_membership.id}/",
            {"role": "ADMIN"},
            format="json"
        )
        self.assertEqual(resp_admin.status_code, status.HTTP_403_FORBIDDEN)

        # Owner promotes member to ADMIN -> 200
        self.client.force_authenticate(user=self.owner)
        resp_owner = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.member_membership.id}/",
            {"role": "ADMIN"},
            format="json"
        )
        self.assertEqual(resp_owner.status_code, status.HTTP_200_OK)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, WorkspaceMembership.Role.ADMIN)

    def test_ownership_transfer_rejected_through_ordinary_role_update(self):
        """Assigning OWNER role through role update must be rejected."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.member_membership.id}/",
            {"role": "OWNER"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_cannot_demote_themselves(self):
        """Owner cannot change their own role to ADMIN or MEMBER."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.owner_membership.id}/",
            {"role": "ADMIN"},
            format="json"
        )
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_admin_cannot_remove_owner_or_admin(self):
        """Admin cannot remove Owner or another Admin."""
        self.client.force_authenticate(user=self.admin)
        # Attempt to delete owner
        resp_owner = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.owner_membership.id}/"
        )
        self.assertEqual(resp_owner.status_code, status.HTTP_403_FORBIDDEN)

        # Create another admin
        admin2 = User.objects.create_user(email="admin2@example.com", password="Password123!")
        admin2_membership = WorkspaceMembership.objects.create(
            workspace=self.team_workspace,
            user=admin2,
            role=WorkspaceMembership.Role.ADMIN
        )
        resp_admin2 = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{admin2_membership.id}/"
        )
        self.assertEqual(resp_admin2.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_cannot_remove_themselves_through_ordinary_deletion(self):
        """Owner cannot delete their own membership."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.owner_membership.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_remove_ordinary_member(self):
        """Admin can remove an ordinary Member."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.member_membership.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WorkspaceMembership.objects.filter(id=self.member_membership.id).exists())

    def test_owner_can_remove_ordinary_member_and_admin(self):
        """Owner can remove both Admin and Member."""
        self.client.force_authenticate(user=self.owner)
        resp_admin = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.admin_membership.id}/"
        )
        self.assertEqual(resp_admin.status_code, status.HTTP_204_NO_CONTENT)

        resp_member = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.member_membership.id}/"
        )
        self.assertEqual(resp_member.status_code, status.HTTP_204_NO_CONTENT)

    def test_cross_workspace_membership_uuid_manipulation_rejected(self):
        """Accessing a membership with mismatched workspace_id in URL must return 404."""
        self.client.force_authenticate(user=self.owner)
        # Attempt to access other_workspace membership under team_workspace URL
        response = self.client.get(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.other_owner_membership.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/memberships/{self.other_owner_membership.id}/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProjectLifecycleAndSecurityTests(BaseWorkspaceAPITestCase):
    """Tests for project creation, unique constraints, authorization, and IDOR prevention."""

    def setUp(self):
        super().setUp()
        self.project_alpha = Project.objects.create(
            workspace=self.team_workspace,
            name="Project Alpha",
            description="Alpha description"
        )
        self.project_beta = Project.objects.create(
            workspace=self.other_workspace,
            name="Project Beta",
            description="Beta description"
        )

    def test_owner_and_admin_can_create_projects(self):
        """OWNER and ADMIN can create projects."""
        self.client.force_authenticate(user=self.owner)
        resp_owner = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/",
            {"name": "Owner Project", "description": "Created by owner"},
            format="json"
        )
        self.assertEqual(resp_owner.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_owner.data["name"], "Owner Project")
        self.assertEqual(resp_owner.data["description"], "Created by owner")

        self.client.force_authenticate(user=self.admin)
        resp_admin = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/",
            {"name": "Admin Project"},
            format="json"
        )
        self.assertEqual(resp_admin.status_code, status.HTTP_201_CREATED)

    def test_member_cannot_create_projects(self):
        """MEMBER cannot create projects."""
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/",
            {"name": "Member Project"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_all_workspace_members_can_view_projects(self):
        """Owner, Admin, and Member can list and retrieve projects in their workspace."""
        for user in [self.owner, self.admin, self.member]:
            self.client.force_authenticate(user=user)
            resp_list = self.client.get(f"/api/v1/workspaces/{self.team_workspace.id}/projects/")
            self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
            results = self.get_results(resp_list.data)
            self.assertEqual(len(results), 1)

            resp_detail = self.client.get(
                f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_alpha.id}/"
            )
            self.assertEqual(resp_detail.status_code, status.HTTP_200_OK)
            self.assertEqual(resp_detail.data["name"], "Project Alpha")

    def test_non_member_cannot_view_projects(self):
        """Users outside workspace cannot list or retrieve projects."""
        self.client.force_authenticate(user=self.outsider)
        resp_list = self.client.get(f"/api/v1/workspaces/{self.team_workspace.id}/projects/")
        self.assertEqual(resp_list.status_code, status.HTTP_403_FORBIDDEN)

        resp_detail = self.client.get(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_alpha.id}/"
        )
        self.assertEqual(resp_detail.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_and_admin_can_update_and_delete_projects(self):
        """Owner and Admin can update and delete projects."""
        # Admin updates
        self.client.force_authenticate(user=self.admin)
        resp_update = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_alpha.id}/",
            {"description": "Updated by admin"},
            format="json"
        )
        self.assertEqual(resp_update.status_code, status.HTTP_200_OK)
        self.project_alpha.refresh_from_db()
        self.assertEqual(self.project_alpha.description, "Updated by admin")

        # Owner deletes
        self.client.force_authenticate(user=self.owner)
        resp_delete = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_alpha.id}/"
        )
        self.assertEqual(resp_delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=self.project_alpha.id).exists())

    def test_member_cannot_update_or_delete_projects(self):
        """Member cannot update or delete projects."""
        self.client.force_authenticate(user=self.member)
        resp_update = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_alpha.id}/",
            {"description": "Hacked by member"},
            format="json"
        )
        self.assertEqual(resp_update.status_code, status.HTTP_403_FORBIDDEN)

        resp_delete = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_alpha.id}/"
        )
        self.assertEqual(resp_delete.status_code, status.HTTP_403_FORBIDDEN)

    def test_client_supplied_workspace_id_cannot_override_url_workspace(self):
        """Client supplying another workspace ID in body cannot override the URL workspace."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/",
            {
                "name": "Spoofed Workspace Project",
                "workspace": str(self.other_workspace.id)
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(id=response.data["id"])
        self.assertEqual(project.workspace, self.team_workspace)
        self.assertNotEqual(project.workspace, self.other_workspace)

    def test_duplicate_project_names_within_same_workspace_rejected(self):
        """Duplicate project names within the same workspace must return 400 Bad Request."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/",
            {"name": "Project Alpha"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_project_name_in_different_workspaces_allowed(self):
        """The same project name can exist in different workspaces."""
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(
            f"/api/v1/workspaces/{self.other_workspace.id}/projects/",
            {"name": "Project Alpha"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Project.objects.filter(workspace=self.other_workspace, name="Project Alpha").exists()
        )

    def test_cross_workspace_project_access_rejected(self):
        """Accessing a project with a mismatched workspace ID in URL must return 404."""
        self.client.force_authenticate(user=self.owner)
        # Attempt to access project_beta (belongs to other_workspace) via team_workspace URL
        resp_get = self.client.get(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_beta.id}/"
        )
        self.assertEqual(resp_get.status_code, status.HTTP_404_NOT_FOUND)

        resp_patch = self.client.patch(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_beta.id}/",
            {"description": "Malicious edit"},
            format="json"
        )
        self.assertEqual(resp_patch.status_code, status.HTTP_404_NOT_FOUND)

        resp_delete = self.client.delete(
            f"/api/v1/workspaces/{self.team_workspace.id}/projects/{self.project_beta.id}/"
        )
        self.assertEqual(resp_delete.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_or_invalid_workspace_id_returns_appropriate_response(self):
        """Non-existent or malformed workspace ID returns 404."""
        self.client.force_authenticate(user=self.owner)
        non_existent_uuid = uuid.uuid4()
        response = self.client.get(f"/api/v1/workspaces/{non_existent_uuid}/projects/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(f"/api/v1/workspaces/{non_existent_uuid}/memberships/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
