"""Test configuration and fixtures."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """
    Return an API client for testing.
    
    Returns:
        APIClient instance
    """
    return APIClient()


@pytest.fixture
def user(db):
    """
    Create and return a test user.
    
    Args:
        db: pytest-django database fixture
        
    Returns:
        User instance
    """
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """
    Return an authenticated API client.
    
    Args:
        api_client: API client fixture
        user: User fixture
        
    Returns:
        Authenticated APIClient instance
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_user(db):
    """
    Create and return an admin user.
    
    Args:
        db: pytest-django database fixture
        
    Returns:
        Admin User instance
    """
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )
