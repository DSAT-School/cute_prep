"""
Views for simplified role-based access control admin panel.
Custom admin UI without Django admin.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from apps.core.models import Role, User
from apps.core.decorators import admin_required, instructor_required
from apps.core.forms_instructor import QuestionForm
from apps.practice.models import Question


@login_required
@admin_required
def rbac_dashboard(request):
    """
    Main RBAC dashboard showing overview of roles and users.
    """
    context = {
        'roles': Role.objects.annotate(user_count=Count('users')).order_by('-weight'),
        'total_users': User.objects.count(),
        'users_by_role': Role.objects.annotate(count=Count('users')).values('name', 'count'),
    }
    return render(request, 'admin/rbac_dashboard.html', context)


@login_required
@admin_required
def role_list(request):
    """
    List all roles with user counts.
    """
    roles = Role.objects.annotate(user_count=Count('users')).order_by('-weight')
    context = {'roles': roles}
    return render(request, 'admin/role_list.html', context)


@login_required
@admin_required
def role_create(request):
    """
    Create a new role.
    """
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        weight = request.POST.get('weight', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validation
        errors = []
        if not name:
            errors.append("Role name is required")
        if not weight:
            errors.append("Role weight is required")
        else:
            try:
                weight = int(weight)
                if weight < 1:
                    errors.append("Role weight must be at least 1")
            except ValueError:
                errors.append("Role weight must be a number")
        
        # Check for duplicates
        if name and Role.objects.filter(name=name).exists():
            errors.append(f"Role '{name}' already exists")
        if weight and Role.objects.filter(weight=weight).exists():
            errors.append(f"Role with weight {weight} already exists")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('core:role_list')
        
        # Create role
        role = Role.objects.create(
            name=name,
            weight=weight,
            description=description
        )
        messages.success(request, f"Role '{role.name}' created successfully!")
        return redirect('core:role_list')
    
    return redirect('core:role_list')


@login_required
@admin_required
def role_edit(request, role_id):
    """
    Edit an existing role.
    """
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        weight = request.POST.get('weight', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # Validation
        errors = []
        if not name:
            errors.append("Role name is required")
        if not weight:
            errors.append("Role weight is required")
        else:
            try:
                weight = int(weight)
                if weight < 1:
                    errors.append("Role weight must be at least 1")
            except ValueError:
                errors.append("Role weight must be a number")
        
        # Check for duplicates (excluding current role)
        if name and Role.objects.filter(name=name).exclude(id=role_id).exists():
            errors.append(f"Role '{name}' already exists")
        if weight and Role.objects.filter(weight=weight).exclude(id=role_id).exists():
            errors.append(f"Role with weight {weight} already exists")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('core:role_list')
        
        # Update role
        role.name = name
        role.weight = weight
        role.description = description
        role.is_active = is_active
        role.save()
        
        messages.success(request, f"Role '{role.name}' updated successfully!")
        return redirect('core:role_list')
    
    return redirect('core:role_list')


@login_required
@admin_required
@require_http_methods(["POST"])
def role_delete(request, role_id):
    """
    Delete a role (if no users are assigned).
    """
    role = get_object_or_404(Role, id=role_id)
    
    # Check if role has users
    if role.users.exists():
        messages.error(request, f"Cannot delete '{role.name}' - it has {role.users.count()} user(s) assigned")
        return redirect('core:role_list')
    
    role_name = role.name
    role.delete()
    messages.success(request, f"Role '{role_name}' deleted successfully!")
    return redirect('core:role_list')


@login_required
@admin_required
def user_role_management(request):
    """
    Manage user role assignments.
    """
    # Search and filter
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.select_related('role').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role_id=role_filter)
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'roles': Role.objects.all().order_by('weight'),
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'admin/user_role_management.html', context)


@login_required
@admin_required
@require_http_methods(["POST"])
def assign_user_role(request, user_id):
    """
    Assign a role to a user.
    """
    user = get_object_or_404(User, id=user_id)
    role_id = request.POST.get('role_id')
    
    if not role_id:
        messages.error(request, "No role selected")
        return redirect('core:user_role_management')
    
    role = get_object_or_404(Role, id=role_id)
    
    # Prevent non-superusers from assigning roles higher than their own
    if not request.user.is_superuser:
        if role.weight > request.user.get_role_weight():
            messages.error(request, "You cannot assign a role higher than your own")
            return redirect('core:user_role_management')
    
    user.role = role
    user.save()
    
    messages.success(request, f"Assigned '{role.name}' role to {user.username}")
    return redirect('core:user_role_management')


@login_required
@admin_required
@require_http_methods(["POST"])
def remove_user_role(request, user_id):
    """
    Remove role from a user (set to default User role).
    """
    user = get_object_or_404(User, id=user_id)
    
    # Get default User role
    try:
        default_role = Role.objects.get(name="User")
        user.role = default_role
        user.save()
        messages.success(request, f"Reset {user.username} to default User role")
    except Role.DoesNotExist:
        user.role = None
        user.save()
        messages.warning(request, f"Removed role from {user.username} (no default role found)")
    
    return redirect('core:user_role_management')


@login_required
@instructor_required
def instructor_dashboard(request):
    """
    Instructor dashboard - accessible to instructors (weight 5+) and admins.
    """
    context = {
        'total_students': User.objects.filter(role__weight__lte=1).count(),
        'total_instructors': User.objects.filter(role__weight__gte=5, role__weight__lt=10).count(),
        'total_questions': Question.objects.count(),
        'active_questions': Question.objects.filter(is_active=True).count(),
    }
    return render(request, 'admin/instructor_dashboard.html', context)


@login_required
@instructor_required
def instructor_question_list(request):
    """
    List all questions with filtering options and pagination.
    Accessible to instructors (weight 5+) and admins.
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    questions = Question.objects.all().order_by('-created_at')
    
    # Apply filters
    domain_filter = request.GET.get('domain')
    skill_filter = request.GET.get('skill')
    type_filter = request.GET.get('type')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q')
    
    if domain_filter:
        questions = questions.filter(domain_code=domain_filter)
    
    if skill_filter:
        questions = questions.filter(skill_code=skill_filter)
    
    if type_filter:
        questions = questions.filter(question_type=type_filter)
    
    if status_filter == 'active':
        questions = questions.filter(is_active=True)
    elif status_filter == 'inactive':
        questions = questions.filter(is_active=False)
    
    if search_query:
        questions = questions.filter(
            Q(identifier_id__icontains=search_query) |
            Q(domain_name__icontains=search_query) |
            Q(skill_name__icontains=search_query) |
            Q(stem__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(questions, 25)  # 25 questions per page
    page = request.GET.get('page')
    
    try:
        questions_page = paginator.page(page)
    except PageNotAnInteger:
        questions_page = paginator.page(1)
    except EmptyPage:
        questions_page = paginator.page(paginator.num_pages)
    
    # Get unique domains and skills for filters
    domains = Question.objects.values_list('domain_code', 'domain_name').distinct().order_by('domain_code')
    skills = Question.objects.values_list('skill_code', 'skill_name').distinct().order_by('skill_code')
    
    context = {
        'questions': questions_page,
        'domains': domains,
        'skills': skills,
        'current_filters': {
            'domain': domain_filter,
            'skill': skill_filter,
            'type': type_filter,
            'status': status_filter,
            'q': search_query,
        }
    }
    return render(request, 'admin/instructor_question_list.html', context)


@login_required
@instructor_required
def instructor_question_create(request):
    """
    Create a new question (general - for both English and Math).
    Accessible to instructors (weight 5+) and admins.
    """
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            messages.success(request, f'Question "{question.identifier_id}" created successfully!')
            return redirect('instructor_question_list')
    else:
        form = QuestionForm()
    
    context = {
        'form': form,
        'action': 'Create',
        'form_url': 'instructor_question_create',
        'subject': None,
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
def instructor_question_create_english(request):
    """
    Create a new English question.
    Accessible to instructors (weight 5+) and admins.
    """
    if request.method == 'POST':
        form = QuestionForm(request.POST, subject='english')
        if form.is_valid():
            question = form.save()
            messages.success(request, f'English Question "{question.identifier_id}" created successfully!')
            return redirect('instructor_question_list')
    else:
        form = QuestionForm(subject='english')
    
    context = {
        'form': form,
        'action': 'Create',
        'form_url': 'instructor_question_create_english',
        'subject': 'english',
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
def instructor_question_create_math(request):
    """
    Create a new Math question.
    Accessible to instructors (weight 5+) and admins.
    """
    if request.method == 'POST':
        form = QuestionForm(request.POST, subject='math')
        if form.is_valid():
            question = form.save()
            messages.success(request, f'Math Question "{question.identifier_id}" created successfully!')
            return redirect('instructor_question_list')
    else:
        form = QuestionForm(subject='math')
    
    context = {
        'form': form,
        'action': 'Create',
        'form_url': 'instructor_question_create_math',
        'subject': 'math',
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
def instructor_question_edit(request, question_id):
    """
    Edit an existing question (general).
    Accessible to instructors (weight 5+) and admins.
    """
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            messages.success(request, f'Question "{question.identifier_id}" updated successfully!')
            return redirect('instructor_question_list')
    else:
        form = QuestionForm(instance=question)
    
    context = {
        'form': form,
        'question': question,
        'action': 'Edit',
        'form_url': 'instructor_question_edit',
        'subject': None,
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
def instructor_question_edit_english(request, question_id):
    """
    Edit an existing English question.
    Accessible to instructors (weight 5+) and admins.
    """
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question, subject='english')
        if form.is_valid():
            question = form.save()
            messages.success(request, f'English Question "{question.identifier_id}" updated successfully!')
            return redirect('instructor_question_list')
    else:
        form = QuestionForm(instance=question, subject='english')
    
    context = {
        'form': form,
        'question': question,
        'action': 'Edit',
        'form_url': 'instructor_question_edit_english',
        'subject': 'english',
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
def instructor_question_edit_math(request, question_id):
    """
    Edit an existing Math question.
    Accessible to instructors (weight 5+) and admins.
    """
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question, subject='math')
        if form.is_valid():
            question = form.save()
            messages.success(request, f'Math Question "{question.identifier_id}" updated successfully!')
            return redirect('instructor_question_list')
    else:
        form = QuestionForm(instance=question, subject='math')
    
    context = {
        'form': form,
        'question': question,
        'action': 'Edit',
        'form_url': 'instructor_question_edit_math',
        'subject': 'math',
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
@require_http_methods(["POST"])
def instructor_question_delete(request, question_id):
    """
    Delete a question.
    Accessible to instructors (weight 5+) and admins.
    """
    question = get_object_or_404(Question, id=question_id)
    identifier = question.identifier_id
    question.delete()
    messages.success(request, f'Question "{identifier}" deleted successfully!')
    return redirect('instructor_question_list')


@login_required
@instructor_required
@require_http_methods(["POST"])
def instructor_question_toggle_status(request, question_id):
    """
    Toggle question active/inactive status.
    Accessible to instructors (weight 5+) and admins.
    """
    question = get_object_or_404(Question, id=question_id)
    question.is_active = not question.is_active
    question.save()
    
    status = "activated" if question.is_active else "deactivated"
    messages.success(request, f'Question "{question.identifier_id}" {status} successfully!')
    return redirect('instructor_question_list')


# ====================
# USER MANAGEMENT VIEWS
# ====================

@login_required
@admin_required
def user_management(request):
    """
    Comprehensive user management dashboard.
    Shows all users with ability to edit, deactivate, delete, and manage onboarding settings.
    """
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    role_filter = request.GET.get('role', 'all')
    
    # Base queryset
    users = User.objects.all().select_related('role')
    
    # Apply search
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Apply role filter
    if role_filter != 'all':
        users = users.filter(role__name=role_filter)
    
    # Order by date joined (newest first)
    users = users.order_by('-date_joined')
    
    # Get all roles for filter dropdown
    roles = Role.objects.all().order_by('name')
    
    # Get onboarding status from cache
    from django.core.cache import cache
    onboarding_enabled = cache.get('user_onboarding_enabled', True)
    
    context = {
        'users': users,
        'roles': roles,
        'search_query': search_query,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'inactive_users': User.objects.filter(is_active=False).count(),
        'onboarding_enabled': onboarding_enabled,
    }
    
    return render(request, 'admin/user_management.html', context)


@login_required
@admin_required
def user_edit(request, user_id):
    """
    Edit user details.
    """
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user fields
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', user.email)
        user.username = request.POST.get('username', user.username)
        
        try:
            user.save()
            messages.success(request, f'User {user.email} updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
        
        return redirect('user_management')
    
    return redirect('user_management')


@login_required
@admin_required
@require_http_methods(["POST"])
def user_toggle_status(request, user_id):
    """
    Activate or deactivate a user.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == request.user.id:
        messages.error(request, 'You cannot deactivate your own account!')
        return redirect('user_management')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f'User {user.email} has been {status}!')
    
    return redirect('user_management')


@login_required
@admin_required
@require_http_methods(["POST"])
def user_delete(request, user_id):
    """
    Delete a user permanently.
    """
    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from deleting themselves
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account!')
        return redirect('user_management')
    
    email = user.email
    user.delete()
    messages.success(request, f'User {email} has been permanently deleted!')
    
    return redirect('user_management')


@login_required
@admin_required
@require_http_methods(["POST"])
def toggle_onboarding(request):
    """
    Toggle new user registration on/off.
    Controls whether new users can sign up via regular signup or OAuth.
    """
    from django.core.cache import cache
    
    current_status = cache.get('user_onboarding_enabled', True)
    new_status = not current_status
    cache.set('user_onboarding_enabled', new_status, None)  # None means no expiry
    
    if new_status:
        status_text = "enabled"
        detail_text = "New users can now register and create accounts."
    else:
        status_text = "disabled"
        detail_text = "New user registration has been blocked. Only existing users can log in."
    
    messages.success(request, f'User registration has been {status_text}! {detail_text}')
    
    return redirect('user_management')
