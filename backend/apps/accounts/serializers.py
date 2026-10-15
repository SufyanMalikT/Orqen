from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id','email','first_name','last_name','password']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.first_name = self.validated_data.get('first_name')
        instance.last_name = self.validated_data.get('last_name')
        return instance

