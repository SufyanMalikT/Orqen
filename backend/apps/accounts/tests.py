"""
Tests for accounts app: custom User model, UserManager, and Admin configuration.
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase

from apps.accounts.admin import UserAdmin
from apps.accounts.forms import CustomUserChangeForm, CustomUserCreationForm
from apps.accounts.models import User


class UserModelConfigTests(SimpleTestCase):
    """Verify custom User model configuration and settings integration."""

    def test_auth_user_model_setting(self):
        """AUTH_USER_MODEL should point to accounts.User."""
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_get_user_model_returns_custom_user(self):
        """get_user_model() should resolve to the accounts.User class."""
        self.assertIs(get_user_model(), User)

    def test_username_field_is_email(self):
        """USERNAME_FIELD must be configured to 'email'."""
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields_is_empty(self):
        """REQUIRED_FIELDS should be empty so only email and password are required."""
        self.assertEqual(User.REQUIRED_FIELDS, [])

    def test_username_field_removed(self):
        """Username field should be None and not present in model fields."""
        field_names = [f.name for f in User._meta.get_fields()]
        self.assertNotIn("username", field_names)
        self.assertIn("email", field_names)

    def test_user_str_representation(self):
        """String representation of a user should be the email address."""
        user = User(email="developer@orqen.dev")
        self.assertEqual(str(user), "developer@orqen.dev")


class UserManagerTests(SimpleTestCase):
    """Verify UserManager behavior for user and superuser creation validation."""

    def test_create_user_object_without_email_raises_error(self):
        """Creating a user without an email must raise ValueError."""
        with self.assertRaisesMessage(ValueError, "The Email field must be set"):
            User.objects._create_user_object(email="", password="secure-password")

    def test_create_user_object_normalizes_email(self):
        """Email domain should be converted to lowercase."""
        user = User.objects._create_user_object(
            email="TEST@EXAMPLE.COM", password="secure-password"
        )
        self.assertEqual(user.email, "TEST@example.com")
        self.assertTrue(user.check_password("secure-password"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_validation_staff(self):
        """create_superuser must enforce is_staff=True."""
        with self.assertRaisesMessage(ValueError, "Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="admin@example.com",
                password="secure-password",
                is_staff=False,
            )

    def test_create_superuser_validation_superuser(self):
        """create_superuser must enforce is_superuser=True."""
        with self.assertRaisesMessage(
            ValueError, "Superuser must have is_superuser=True."
        ):
            User.objects.create_superuser(
                email="admin@example.com",
                password="secure-password",
                is_superuser=False,
            )


class AdminConfigTests(SimpleTestCase):
    """Verify admin forms and UserAdmin registration."""

    def test_custom_user_admin_registered(self):
        """User model should be registered with UserAdmin."""
        self.assertIn(User, admin.site._registry)
        self.assertIsInstance(admin.site._registry[User], UserAdmin)

    def test_admin_forms_configuration(self):
        """Forms should use User model and omit username."""
        self.assertIs(UserAdmin.add_form, CustomUserCreationForm)
        self.assertIs(UserAdmin.form, CustomUserChangeForm)
        self.assertNotIn("username", CustomUserCreationForm().fields)
        self.assertIn("email", CustomUserCreationForm().fields)

    def test_admin_fieldsets_contain_email_not_username(self):
        """UserAdmin fieldsets and add_fieldsets should reference email instead of username."""
        admin_instance = admin.site._registry[User]
        flattened_fields = [
            f for _, fieldset in admin_instance.fieldsets for f in fieldset["fields"]
        ]
        self.assertIn("email", flattened_fields)
        self.assertNotIn("username", flattened_fields)

        flattened_add_fields = [
            f
            for _, fieldset in admin_instance.add_fieldsets
            for f in fieldset["fields"]
        ]
        self.assertIn("email", flattened_add_fields)
        self.assertNotIn("username", flattened_add_fields)
