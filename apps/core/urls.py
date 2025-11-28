"""URL configuration for core application."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, dashboard_view, health_check, set_timezone

app_name = "core"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("set-timezone/", set_timezone, name="set-timezone"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("", include(router.urls)),
]
