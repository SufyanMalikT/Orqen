from django.shortcuts import render
from rest_framework.generics  import CreateAPIView, RetrieveUpdateAPIView
from .models import User
from .serializers import UserSerializer, UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
# Create your views here.

class UserRegistrationView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(status=400,data={'message':'Refresh token is required'})

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except:
            raise ValidationError({'message':'Invalid refresh token'})
        return Response(status=205)

        
class UserProfileRetrieveView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

