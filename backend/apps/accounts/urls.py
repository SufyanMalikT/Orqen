from django.urls import path
from .views import UserRegistrationView, UserLogoutView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
urlpatterns = [
    path('auth/register/', UserRegistrationView.as_view(), name='singup'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/logout/',UserLogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),

]