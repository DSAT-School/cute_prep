"""Integration tests for User API endpoints."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from tests.factories import UserFactory

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db
class TestUserViewSet:
    """Test cases for User ViewSet."""

    def test_list_users_authenticated_success(self, authenticated_client):
        """Test listing users as authenticated user."""
        UserFactory.create_batch(5)
        response = authenticated_client.get("/api/users/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 5

    def test_list_users_unauthenticated_forbidden(self, api_client):
        """Test listing users as unauthenticated user is forbidden."""
        response = api_client.get("/api/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_user_success(self, api_client):
        """Test creating a new user."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "password_confirm": "newpass123",
            "first_name": "New",
            "last_name": "User"
        }
        response = api_client.post("/api/users/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newuser").exists()

    def test_create_user_password_mismatch_fails(self, api_client):
        """Test creating user with mismatched passwords fails."""
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "password_confirm": "different123",
        }
        response = api_client.post("/api/users/", data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_user_authenticated_success(self, authenticated_client, user):
        """Test retrieving specific user as authenticated user."""
        response = authenticated_client.get(f"/api/users/{user.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username

    def test_get_current_user_success(self, authenticated_client, user):
        """Test retrieving current authenticated user."""
        response = authenticated_client.get("/api/users/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_update_user_success(self, authenticated_client, user):
        """Test updating user information."""
        data = {
            "first_name": "Updated",
            "last_name": "Name"
        }
        response = authenticated_client.patch(f"/api/users/{user.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.last_name == "Name"

    def test_delete_user_success(self, authenticated_client):
        """Test deleting a user."""
        user_to_delete = UserFactory()
        response = authenticated_client.delete(f"/api/users/{user_to_delete.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(id=user_to_delete.id).exists()


@pytest.mark.integration
@pytest.mark.django_db
class TestHealthCheckEndpoint:
    """Test cases for health check endpoint."""

    def test_health_check_success(self, api_client):
        """Test health check endpoint returns healthy status."""
        response = api_client.get("/api/health/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert response.data["database"] == "connected"
