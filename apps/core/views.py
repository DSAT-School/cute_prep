"""Views for core application."""
from typing import Any

from django.db import connection
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import User
from .serializers import UserCreateSerializer, UserSerializer


def health_check(request: Request) -> JsonResponse:
    """
    Health check endpoint for deployment monitoring.
    
    Checks the status of the application and its dependencies.
    
    Args:
        request: HTTP request object
        
    Returns:
        JSON response with health status
    """
    health_status = {
        "status": "healthy",
        "database": "disconnected",
        "cache": "unknown",
    }
    
    # Check database connection
    try:
        connection.ensure_connection()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
    
    # Check cache connection
    try:
        from django.core.cache import cache
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            health_status["cache"] = "connected"
        else:
            health_status["cache"] = "disconnected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["cache"] = f"error: {str(e)}"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing User instances.
    
    Provides CRUD operations for User model with proper
    authentication and permission checks.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Return appropriate serializer class based on action.
        
        Returns:
            Serializer class to use
        """
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Return appropriate permissions based on action.
        
        Returns:
            List of permission instances
        """
        if self.action == "create":
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request: Request) -> Response:
        """
        Return the current authenticated user's information.
        
        Args:
            request: HTTP request object
            
        Returns:
            Response with user data
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        List all users with pagination.
        
        Args:
            request: HTTP request object
            args: Additional positional arguments
            kwargs: Additional keyword arguments
            
        Returns:
            Response with paginated user list
        """
        return super().list(request, *args, **kwargs)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a specific user.
        
        Args:
            request: HTTP request object
            args: Additional positional arguments
            kwargs: Additional keyword arguments
            
        Returns:
            Response with user data
        """
        return super().retrieve(request, *args, **kwargs)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new user.
        
        Args:
            request: HTTP request object
            args: Additional positional arguments
            kwargs: Additional keyword arguments
            
        Returns:
            Response with created user data
        """
        return super().create(request, *args, **kwargs)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Update a user.
        
        Args:
            request: HTTP request object
            args: Additional positional arguments
            kwargs: Additional keyword arguments
            
        Returns:
            Response with updated user data
        """
        return super().update(request, *args, **kwargs)

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a user.
        
        Args:
            request: HTTP request object
            args: Additional positional arguments
            kwargs: Additional keyword arguments
            
        Returns:
            Response with no content
        """
        return super().destroy(request, *args, **kwargs)
