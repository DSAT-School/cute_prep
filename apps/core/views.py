"""Views for core application."""
import json
from typing import Any

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages import get_messages
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import CreateView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .forms import (
    CustomLoginForm,
    CustomPasswordChangeForm,
    CustomSetPasswordForm,
    CustomSignupForm,
    ProfileUpdateForm,
)
from .models import User
from .serializers import UserCreateSerializer, UserSerializer
from .utils.timezone import validate_timezone


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


@require_POST
@csrf_exempt
def set_timezone(request: Request) -> JsonResponse:
    """
    Set user's detected timezone in session.
    
    Called by client-side JavaScript to store the browser-detected timezone.
    This timezone will be used by TimezoneMiddleware for datetime display.
    
    Args:
        request: HTTP request object with JSON body containing 'timezone'
        
    Returns:
        JSON response with success status
    """
    try:
        data = json.loads(request.body)
        timezone = data.get('timezone', 'UTC')
        
        # Validate timezone
        if not validate_timezone(timezone):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid timezone'
            }, status=400)
        
        # Store in session
        request.session['detected_timezone'] = timezone
        
        # If user is authenticated, optionally update their profile
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'timezone'):
                # Only update if user hasn't explicitly set a timezone
                if request.user.timezone == 'UTC':
                    request.user.timezone = timezone
                    request.user.save(update_fields=['timezone'])
        
        return JsonResponse({
            'status': 'success',
            'timezone': timezone
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


class CustomLoginView(LoginView):
    """
    Custom login view with email/username support.
    """
    template_name = "auth/login.html"
    form_class = CustomLoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy("dashboard")


class CustomSignupView(CreateView):
    """
    Custom registration view.
    """
    template_name = "auth/signup.html"
    form_class = CustomSignupForm
    success_url = reverse_lazy("dashboard")
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log the user in after successful registration
        login(self.request, self.object)
        return response
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)


class CustomLogoutView(LogoutView):
    """
    Custom logout view.
    Allows both GET and POST methods for compatibility.
    """
    next_page = "landing"
    http_method_names = ['get', 'post', 'options']


@login_required
def delta_store_view(request):
    """
    Delta Store view where users can purchase items with Delta coins.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered Delta store template
    """
    return render(request, 'delta/store.html')


@login_required
def dashboard_view(request):
    """
    Dashboard view for authenticated users with comprehensive analytics.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered dashboard template with performance insights
    """
    from apps.practice.models import PracticeSession, UserAnswer, Question
    from django.db.models import Count, Avg, Q, F
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    user = request.user
    
    # Get all completed sessions
    sessions = PracticeSession.objects.filter(
        user=user,
        status='completed'
    ).order_by('-completed_at')
    
    # Calculate total stats
    total_sessions = sessions.count()
    total_questions = UserAnswer.objects.filter(user=user).count()
    correct_answers = UserAnswer.objects.filter(user=user, is_correct=True).count()
    incorrect_answers = total_questions - correct_answers
    overall_accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Calculate study streak
    study_streak = 0
    if sessions.exists():
        current_date = datetime.now().date()
        for i in range(365):  # Check up to 1 year
            check_date = current_date - timedelta(days=i)
            if sessions.filter(completed_at__date=check_date).exists():
                study_streak += 1
            else:
                break
    
    # Get recent sessions (last 5)
    recent_sessions = sessions[:5]
    
    # Analyze performance by domain
    domain_stats = UserAnswer.objects.filter(user=user).values(
        'question__domain_name', 'question__domain_code'
    ).annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
        incorrect=Count('id', filter=Q(is_correct=False))
    ).order_by('-incorrect')
    
    # Calculate accuracy for each domain
    for stat in domain_stats:
        stat['accuracy'] = (stat['correct'] / stat['total'] * 100) if stat['total'] > 0 else 0
    
    # Analyze performance by skill
    skill_stats = UserAnswer.objects.filter(user=user).values(
        'question__skill_name', 'question__skill_code', 'question__domain_code'
    ).annotate(
        total=Count('id'),
        correct=Count('id', filter=Q(is_correct=True)),
        incorrect=Count('id', filter=Q(is_correct=False))
    ).order_by('-incorrect')
    
    # Calculate accuracy for each skill
    for stat in skill_stats:
        stat['accuracy'] = (stat['correct'] / stat['total'] * 100) if stat['total'] > 0 else 0
    
    # Identify weak areas (skills with accuracy < 70% and at least 3 questions attempted)
    weak_skills = [s for s in skill_stats if s['accuracy'] < 70 and s['total'] >= 3][:5]
    
    # Identify strong areas (skills with accuracy >= 80% and at least 5 questions)
    strong_skills = [s for s in skill_stats if s['accuracy'] >= 80 and s['total'] >= 5][:3]
    
    # Get recommended practice topics (weak skills with available questions)
    recommendations = []
    for weak_skill in weak_skills[:3]:
        # Count available questions for this skill
        available_count = Question.objects.filter(
            skill_code=weak_skill['question__skill_code']
        ).exclude(
            user_answers__user=user
        ).count()
        
        if available_count > 0:
            recommendations.append({
                'skill_name': weak_skill['question__skill_name'],
                'skill_code': weak_skill['question__skill_code'],
                'domain_code': weak_skill['question__domain_code'],
                'accuracy': weak_skill['accuracy'],
                'total_attempted': weak_skill['total'],
                'available_questions': available_count,
                'priority': 'high' if weak_skill['accuracy'] < 50 else 'medium'
            })
    
    # If no weak areas, recommend untried skills
    if not recommendations:
        untried_skills = Question.objects.exclude(
            user_answers__user=user
        ).values('skill_name', 'skill_code', 'domain_code').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        for skill in untried_skills:
            recommendations.append({
                'skill_name': skill['skill_name'],
                'skill_code': skill['skill_code'],
                'domain_code': skill['domain_code'],
                'accuracy': None,
                'total_attempted': 0,
                'available_questions': skill['count'],
                'priority': 'explore'
            })
    
    # Calculate estimated SAT score (rough estimation: 200-800 scale)
    # Each section (Math, Reading & Writing) is 200-800
    estimated_score = None
    if total_questions >= 10:  # Only estimate if enough data
        base_score = 200
        accuracy_bonus = (overall_accuracy / 100) * 600
        estimated_score = int(base_score + accuracy_bonus)
    
    context = {
        'user': user,
        'total_sessions': total_sessions,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'overall_accuracy': round(overall_accuracy, 1),
        'study_streak': study_streak,
        'estimated_score': estimated_score,
        'recent_sessions': recent_sessions,
        'domain_stats': domain_stats,
        'weak_skills': weak_skills,
        'strong_skills': strong_skills,
        'recommendations': recommendations,
    }
    return render(request, 'dashboard.html', context)


def profile_view(request):
    """
    Profile management view for authenticated users.
    
    Handles:
    - Profile information display and update
    - Password change for existing users
    - Password creation for OAuth users
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered profile template with forms
    """
    @login_required
    def _profile(request):
        user = request.user
        
        # Check if user has a usable password (not OAuth-only user)
        has_password = user.has_usable_password()
        
        # Initialize forms
        profile_form = ProfileUpdateForm(instance=user)
        password_form = None
        
        if has_password:
            password_form = CustomPasswordChangeForm(user=user)
        else:
            password_form = CustomSetPasswordForm(user=user)
        
        # Handle form submissions
        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            
            if form_type == 'profile':
                profile_form = ProfileUpdateForm(request.POST, instance=user, user=user)
                if profile_form.is_valid():
                    profile_form.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('profile')
                else:
                    messages.error(request, 'Please correct the errors below.')
            
            elif form_type == 'password':
                if has_password:
                    password_form = CustomPasswordChangeForm(user=user, data=request.POST)
                else:
                    password_form = CustomSetPasswordForm(user=user, data=request.POST)
                
                if password_form.is_valid():
                    saved_user = password_form.save()
                    
                    # Keep user logged in after password change/creation
                    # This updates the session to prevent logout
                    update_session_auth_hash(request, saved_user)
                    
                    # Re-login the user to ensure session is fresh
                    login(request, saved_user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    if has_password:
                        messages.success(request, 'Password changed successfully!')
                    else:
                        messages.success(request, 'Password created successfully! You can now use it to log in.')
                    return redirect('profile')
                else:
                    messages.error(request, 'Please correct the errors below.')
        
        # Check if user signed up via OAuth
        oauth_provider = None
        if hasattr(user, 'socialaccount_set'):
            social_accounts = user.socialaccount_set.all()
            if social_accounts.exists():
                oauth_provider = social_accounts.first().provider
        
        context = {
            'user': user,
            'profile_form': profile_form,
            'password_form': password_form,
            'has_password': has_password,
            'oauth_provider': oauth_provider,
        }
        return render(request, 'profile.html', context)
    
    return _profile(request)
