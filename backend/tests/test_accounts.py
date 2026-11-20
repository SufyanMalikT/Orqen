import os
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User


class UserRegistrationTests(APITestCase):
    """Tests covering user registration endpoint, input validation, and password hashing."""

    def test_register_user_successful(self):
        """Valid registration creates an active user with properly hashed password."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "register_test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "StrongPassword!123"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["email"], "register_test@example.com")
        self.assertNotIn("password", response.data)

        # Verify user in database
        user = User.objects.get(email="register_test@example.com")
        self.assertTrue(user.check_password("StrongPassword!123"))
        self.assertNotEqual(user.password, "StrongPassword!123")
        self.assertTrue(user.is_active)

    def test_duplicate_email_rejected(self):
        """Registering with an already existing email returns 400 Bad Request."""
        User.objects.create_user(email="existing@example.com", password="Password123!")
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "existing@example.com",
                "password": "NewPassword123!"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_invalid_email_format_rejected(self):
        """Malformed email format returns 400 Bad Request."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "not-an-email",
                "password": "Password123!"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields_rejected(self):
        """Registration without email or password returns 400 Bad Request."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {"first_name": "NoEmail"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_rejected(self):
        """Password failing Django validators (e.g. numeric, too short) returns 400."""
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "weak_pwd@example.com",
                "password": "123"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_newly_registered_user_cannot_access_protected_endpoint_without_auth(self):
        """Newly created user must authenticate with JWT before accessing protected routes."""
        self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "unauthed_check@example.com",
                "password": "Password123!"
            },
            format="json"
        )
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserLoginTests(APITestCase):
    """Tests covering login and JWT generation."""

    def setUp(self):
        self.email = "login_test@example.com"
        self.password = "ValidPassword123!"
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name="Login",
            last_name="Tester"
        )

    def test_successful_login_returns_jwt_pair(self):
        """Valid credentials return HTTP 200 with both access and refresh tokens."""
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": self.email, "password": self.password},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_incorrect_password_rejected(self):
        """Wrong password returns 401 Unauthorized."""
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": self.email, "password": "WrongPassword!"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_user_rejected(self):
        """Non-existent email returns 401 Unauthorized."""
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "nobody@example.com", "password": self.password},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_credentials_rejected(self):
        """Empty payload returns 400 Bad Request."""
        response = self.client.post(
            "/api/v1/auth/login/",
            {},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_cannot_login(self):
        """Deactivated user returns 401 Unauthorized."""
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": self.email, "password": self.password},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenManagementTests(APITestCase):
    """Tests covering token refresh, blacklisting, and logout lifecycle."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="token_user@example.com",
            password="Password123!"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

    def test_successful_token_refresh(self):
        """Valid refresh token yields a new access token."""
        response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": str(self.refresh)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_refresh_token_rejected(self):
        """Bogus refresh token string returns 401 Unauthorized."""
        response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": "invalid-token-value"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_logout_blacklists_token(self):
        """Logout endpoint returns 205 and blacklists the provided refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": str(self.refresh)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Attempting to refresh the blacklisted token must now fail with 401
        refresh_attempt = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": str(self.refresh)},
            format="json"
        )
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_missing_refresh_token_returns_400(self):
        """Calling logout without refresh token in body returns 400 Bad Request."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            "/api/v1/auth/logout/",
            {},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_logout_rejected(self):
        """Logout requires authentication."""
        response = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": str(self.refresh)},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileTests(APITestCase):
    """Tests covering profile retrieval, updates, and protected fields."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="profile_test@example.com",
            password="Strong-Test!123",
            first_name="OriginalFirst",
            last_name="OriginalLast"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

    def test_unauthenticated_cannot_get_profile(self):
        """Unauthenticated profile request returns 401."""
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_retrieves_own_profile(self):
        """Authenticated user receives their own profile details."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], "OriginalFirst")
        self.assertEqual(response.data["last_name"], "OriginalLast")

    def test_user_can_update_permitted_profile_fields(self):
        """User can update first_name and last_name via PATCH."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/v1/users/me/",
            {"first_name": "UpdatedFirst", "last_name": "UpdatedLast"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "UpdatedFirst")
        self.assertEqual(self.user.last_name, "UpdatedLast")

    def test_user_cannot_modify_protected_fields(self):
        """Protected fields like email and id cannot be changed through profile update."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/v1/users/me/",
            {"email": "hacked@example.com", "id": 9999},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile_test@example.com")
        self.assertNotEqual(self.user.id, 9999)


class PasswordChangeTests(APITestCase):
    """Tests covering password change endpoint, validation, and security."""

    def setUp(self):
        self.initial_password = "Strong-Password!123"
        self.user = User.objects.create_user(
            email="pwd_change@example.com",
            password=self.initial_password
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

    def test_unauthenticated_cannot_change_password(self):
        """Unauthenticated user cannot change password."""
        response = self.client.patch(
            "/api/v1/users/me/password/",
            {
                "current_password": self.initial_password,
                "password": "NewStrongPassword!456",
                "confirm_password": "NewStrongPassword!456"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_successful_password_change(self):
        """Valid current and matching new password successfully updates credentials."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/v1/users/me/password/",
            {
                "current_password": self.initial_password,
                "password": "NewStrongPassword!456",
                "confirm_password": "NewStrongPassword!456"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("password", response.data)

        # Verify old password no longer works
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(self.initial_password))
        # Verify new password works
        self.assertTrue(self.user.check_password("NewStrongPassword!456"))

        # Verify login succeeds with new password
        login_resp = self.client.post(
            "/api/v1/auth/login/",
            {"email": "pwd_change@example.com", "password": "NewStrongPassword!456"},
            format="json"
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)

    def test_incorrect_current_password_rejected(self):
        """Supplying wrong current password returns 400 Bad Request."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/v1/users/me/password/",
            {
                "current_password": "WrongCurrentPassword!",
                "password": "NewStrongPassword!456",
                "confirm_password": "NewStrongPassword!456"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data)

    def test_password_confirmation_mismatch_rejected(self):
        """Mismatched confirm_password returns 400 Bad Request."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/v1/users/me/password/",
            {
                "current_password": self.initial_password,
                "password": "NewStrongPassword!456",
                "confirm_password": "DifferentPassword!789"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data)

    def test_weak_new_password_rejected(self):
        """Weak new password failing Django password validators returns 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.patch(
            "/api/v1/users/me/password/",
            {
                "current_password": self.initial_password,
                "password": "123",
                "confirm_password": "123"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
