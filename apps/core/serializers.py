"""Serializers for core models."""
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    
    Handles serialization and deserialization of User instances.
    Excludes sensitive fields like password.
    """

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new User instances.
    
    Includes password field for user creation and handles
    password hashing automatically.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]

    def validate(self, attrs: dict) -> dict:
        """
        Validate that passwords match.
        
        Args:
            attrs: Dictionary of attributes to validate
            
        Returns:
            Validated attributes
            
        Raises:
            serializers.ValidationError: If passwords don't match
        """
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        attrs.pop("password_confirm")
        return attrs

    def create(self, validated_data: dict) -> User:
        """
        Create a new user with encrypted password.
        
        Args:
            validated_data: Validated data for user creation
            
        Returns:
            Created User instance
        """
        user = User.objects.create_user(**validated_data)
        return user
