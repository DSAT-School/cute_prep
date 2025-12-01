"""
URL configuration for practice_portal project.

The `urlpatterns` list routes URLs to views.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.views import (
    CustomLoginView,
    CustomLogoutView,
    CustomSignupView,
    dashboard_view,
    profile_view,
)

urlpatterns = [
    # Landing and Home Pages
    path("", TemplateView.as_view(template_name="landing.html"), name="landing"),
    path("home/", TemplateView.as_view(template_name="home.html"), name="home"),
    
    # Authentication URLs
    path("login/", CustomLoginView.as_view(), name="login"),
    path("signup/", CustomSignupView.as_view(), name="signup"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
    path("accounts/", include("allauth.urls")),
    
    # SSR Pages (Server-Side Rendered)
    path("dashboard/", dashboard_view, name="dashboard"),
    path("profile/", profile_view, name="profile"),
    
    # Practice App
    path("practice/", include("apps.practice.urls")),
    
    # Admin
    path("admin/", admin.site.urls),
    
    # API Endpoints
    path("api/", include("apps.core.urls")),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
