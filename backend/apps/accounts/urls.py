from django.urls import path
from .views import UserRegistrationView, UserLogoutView, UserProfileRetrieveUpdateView, UserPasswordUpdationView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
urlpatterns = [
    path('auth/register/', UserRegistrationView.as_view(), name='singup'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/logout/',UserLogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('users/me/', UserProfileRetrieveUpdateView.as_view(), name='profile'),
    path('users/me/password', UserPasswordUpdationView.as_view(), name='change_password'),
]