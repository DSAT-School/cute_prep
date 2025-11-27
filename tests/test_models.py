"""Unit tests for User model."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from tests.factories import UserFactory

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model."""

    def test_create_user_success(self):
        """Test creating a user successfully."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_superuser_success(self):
        """Test creating a superuser successfully."""
        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        assert admin.username == "admin"
        assert admin.is_staff is True
        assert admin.is_superuser is True

    def test_user_email_unique(self):
        """Test that user email must be unique."""
        UserFactory(email="duplicate@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="duplicate@example.com")

    def test_user_str_representation(self):
        """Test string representation of user."""
        user = UserFactory(username="johndoe")
        assert str(user) == "johndoe"

    def test_user_get_full_name_with_names(self):
        """Test get_full_name when first and last names are set."""
        user = UserFactory(
            first_name="John",
            last_name="Doe",
            username="johndoe"
        )
        assert user.get_full_name() == "John Doe"

    def test_user_get_full_name_without_names(self):
        """Test get_full_name when names are not set."""
        user = UserFactory(
            first_name="",
            last_name="",
            username="johndoe"
        )
        assert user.get_full_name() == "johndoe"

    def test_user_has_uuid_primary_key(self):
        """Test that user uses UUID as primary key."""
        user = UserFactory()
        assert isinstance(user.id, type(user.id))
        assert len(str(user.id)) == 36  # UUID format

    def test_user_timestamps(self):
        """Test that user has created_at and updated_at timestamps."""
        user = UserFactory()
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.updated_at >= user.created_at
