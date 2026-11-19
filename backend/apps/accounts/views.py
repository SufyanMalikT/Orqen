from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .models import User
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    ChangeUserPasswordSerializer,
)


class UserRegistrationView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': 'Refresh token is required.'}
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (TokenError, InvalidToken):
            raise ValidationError({'message': 'Invalid or expired refresh token.'})

        return Response(status=status.HTTP_205_RESET_CONTENT)


class UserProfileRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserPasswordUpdationView(UpdateAPIView):
    serializer_class = ChangeUserPasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(
            {'message': 'Password successfully updated.'},
            status=status.HTTP_200_OK
        )
