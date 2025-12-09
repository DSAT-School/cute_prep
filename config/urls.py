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
    delta_store_view,
    profile_view,
)
from apps.core import views_rbac
from apps.core.ai_chat_views import (
    ai_chat_view,
    ai_chat_message,
    ai_upload_image,
    ai_generate_question,
    ai_chat_history,
    ai_task_status,
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
    path("delta/store/", delta_store_view, name="delta_store"),
    
    # Practice App
    path("practice/", include("apps.practice.urls")),
    
    # AI Chat (SAT Buddy)
    path("ai/chat/", ai_chat_view, name="ai_chat"),
    path("ai/chat/message/", ai_chat_message, name="ai_chat_message"),
    path("ai/task/<str:task_id>/", ai_task_status, name="ai_task_status"),
    path("ai/upload-image/", ai_upload_image, name="ai_upload_image"),
    path("ai/generate-question/", ai_generate_question, name="ai_generate_question"),
    path("ai/chat/history/", ai_chat_history, name="ai_chat_history"),
    
    # RBAC Admin Panel (Simplified - Custom UI, not Django admin)
    path("rbac/", views_rbac.rbac_dashboard, name="rbac_dashboard"),
    path("rbac/roles/", views_rbac.role_list, name="role_list"),
    path("rbac/roles/create/", views_rbac.role_create, name="role_create"),
    path("rbac/roles/<uuid:role_id>/edit/", views_rbac.role_edit, name="role_edit"),
    path("rbac/roles/<uuid:role_id>/delete/", views_rbac.role_delete, name="role_delete"),
    path("rbac/users/", views_rbac.user_role_management, name="user_role_management"),
    path("rbac/users/<uuid:user_id>/assign-role/", views_rbac.assign_user_role, name="assign_user_role"),
    path("rbac/users/<uuid:user_id>/remove-role/", views_rbac.remove_user_role, name="remove_user_role"),
    
    # Instructor Panel
    path("instructor/", views_rbac.instructor_dashboard, name="instructor_dashboard"),
    path("instructor/questions/", views_rbac.instructor_question_list, name="instructor_question_list"),
    path("instructor/questions/create/", views_rbac.instructor_question_create, name="instructor_question_create"),
    path("instructor/questions/create/english/", views_rbac.instructor_question_create_english, name="instructor_question_create_english"),
    path("instructor/questions/create/math/", views_rbac.instructor_question_create_math, name="instructor_question_create_math"),
    path("instructor/questions/<uuid:question_id>/edit/", views_rbac.instructor_question_edit, name="instructor_question_edit"),
    path("instructor/questions/<uuid:question_id>/edit/english/", views_rbac.instructor_question_edit_english, name="instructor_question_edit_english"),
    path("instructor/questions/<uuid:question_id>/edit/math/", views_rbac.instructor_question_edit_math, name="instructor_question_edit_math"),
    path("instructor/questions/<uuid:question_id>/delete/", views_rbac.instructor_question_delete, name="instructor_question_delete"),
    path("instructor/questions/<uuid:question_id>/toggle/", views_rbac.instructor_question_toggle_status, name="instructor_question_toggle"),
    
    # Admin (Django admin - for superusers only)
    path("admin/", admin.site.urls),
    
    # API Endpoints
    path("api/", include("apps.core.urls")),
    path("api/delta/", include("apps.core.urls_delta")),
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

# Custom error handlers
handler404 = 'apps.core.error_handlers.handler404'
handler500 = 'apps.core.error_handlers.handler500'
handler403 = 'apps.core.error_handlers.handler403'
