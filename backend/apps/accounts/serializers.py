from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'password', 'is_active']
        read_only_fields = ['id', 'is_active']

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        return User.objects.create_user(password=password, **validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'email']


class ChangeUserPasswordSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['current_password', 'password', 'confirm_password']

    def validate_password(self, value):
        validate_password(value, user=self.instance)
        return value

    def validate(self, attrs):
        if not attrs.get('current_password') or not attrs.get('password') or not attrs.get('confirm_password'):
            raise serializers.ValidationError('Current password, new password, and confirmation are required.')

        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })

        user = self.instance
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({
                'current_password': 'Incorrect password.'
            })

        return attrs

    def update(self, instance, validated_data):
        password = validated_data['password']
        instance.set_password(password)
        instance.save(update_fields=['password'])
        return instance
