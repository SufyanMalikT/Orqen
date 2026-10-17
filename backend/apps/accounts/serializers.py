from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from rest_framework.exceptions import ValidationError
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name','password','is_active']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name']
        read_only_fields = ['id','email']