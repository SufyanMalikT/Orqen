from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User


class CustomUserCreationForm(AdminUserCreationForm):
    """
    Form for creating a new user in the admin interface using email.
    """

    class Meta(AdminUserCreationForm.Meta):
        model = User
        fields = ("email",)


class CustomUserChangeForm(UserChangeForm):
    """
    Form for updating an existing user in the admin interface.
    """

    class Meta(UserChangeForm.Meta):
        model = User
        fields = "__all__"
