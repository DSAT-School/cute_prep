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
    Create a new question.
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
    }
    return render(request, 'admin/instructor_question_form.html', context)


@login_required
@instructor_required
def instructor_question_edit(request, question_id):
    """
    Edit an existing question.
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
