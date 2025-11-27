"""URL configuration for core application."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, health_check

app_name = "core"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("", include(router.urls)),
]
