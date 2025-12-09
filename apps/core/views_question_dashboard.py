"""
Question Management Dashboard Views
Provides analytics and management interface for questions.
"""

from django.db.models import Count, Q
from django.shortcuts import render
from apps.practice.models import Question
from apps.core.decorators import instructor_required


@instructor_required
def question_dashboard(request):
    """
    Display question management dashboard with statistics and filters.
    Shows total questions, breakdown by subject, contributor stats, etc.
    """
    # Get filter parameters
    subject_filter = request.GET.get('subject', '')
    question_type_filter = request.GET.get('question_type', '')
    difficulty_filter = request.GET.get('difficulty', '')
    domain_filter = request.GET.get('domain', '')
    skill_filter = request.GET.get('skill', '')
    provider_filter = request.GET.get('provider', '')
    is_active_filter = request.GET.get('is_active', '')
    
    # Base queryset
    questions = Question.objects.all()
    
    # Apply filters
    if subject_filter:
        if subject_filter == 'english':
            questions = questions.filter(domain_code__in=['INI', 'CAS', 'EOI', 'SEC'])
        elif subject_filter == 'math':
            questions = questions.filter(domain_code__in=['H', 'P', 'Q', 'S'])
    
    if question_type_filter:
        questions = questions.filter(question_type=question_type_filter)
    
    if difficulty_filter:
        questions = questions.filter(difficulty=difficulty_filter)
    
    if domain_filter:
        questions = questions.filter(domain_code=domain_filter)
    
    if skill_filter:
        questions = questions.filter(skill_code=skill_filter)
    
    if provider_filter:
        questions = questions.filter(provider_code=provider_filter)
    
    if is_active_filter:
        questions = questions.filter(is_active=is_active_filter == 'true')
    
    # Overall statistics
    total_questions = questions.count()
    active_questions = questions.filter(is_active=True).count()
    inactive_questions = questions.filter(is_active=False).count()
    
    # Subject breakdown (English domains vs Math domains)
    # English: INI, CAS, EOI, SEC
    # Math: H (Algebra), P (Advanced Math), Q (Problem-Solving), S (Geometry)
    english_domains = ['INI', 'CAS', 'EOI', 'SEC']
    math_domains = ['H', 'P', 'Q', 'S']
    
    english_count = questions.filter(domain_code__in=english_domains).count()
    math_count = questions.filter(domain_code__in=math_domains).count()
    
    # Question type breakdown
    mcq_count = questions.filter(question_type='MCQ').count()
    spr_count = questions.filter(question_type='SPR').count()
    
    # Difficulty breakdown
    easy_count = questions.filter(difficulty='easy').count()
    medium_count = questions.filter(difficulty='medium').count()
    hard_count = questions.filter(difficulty='hard').count()
    
    # Domain breakdown
    domain_stats = questions.values('domain_code', 'domain_name').annotate(
        count=Count('question_id')
    ).order_by('-count')
    
    # Skill breakdown (top 10)
    skill_stats = questions.values('skill_code', 'skill_name').annotate(
        count=Count('question_id')
    ).order_by('-count')[:10]
    
    # Provider statistics (since created_by field doesn't exist)
    provider_stats = questions.values('provider_name', 'provider_code').annotate(
        total_questions=Count('question_id'),
        active_questions=Count('question_id', filter=Q(is_active=True)),
        mcq_questions=Count('question_id', filter=Q(question_type='MCQ')),
        spr_questions=Count('question_id', filter=Q(question_type='SPR')),
        english_questions=Count('question_id', filter=Q(domain_code__in=english_domains)),
        math_questions=Count('question_id', filter=Q(domain_code__in=math_domains))
    ).order_by('-total_questions')
    
    # Get unique values for filter dropdowns
    all_domains = Question.objects.values_list('domain_code', 'domain_name').distinct().order_by('domain_code')
    all_skills = Question.objects.values_list('skill_code', 'skill_name').distinct().order_by('skill_code')
    all_providers = Question.objects.values_list('provider_code', 'provider_name').distinct().order_by('provider_code')
    
    # Recent questions (latest 20)
    recent_questions = questions.order_by('-created_at')[:20]
    
    context = {
        'total_questions': total_questions,
        'active_questions': active_questions,
        'inactive_questions': inactive_questions,
        'english_count': english_count,
        'math_count': math_count,
        'mcq_count': mcq_count,
        'spr_count': spr_count,
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'domain_stats': domain_stats,
        'skill_stats': skill_stats,
        'provider_stats': provider_stats,
        'recent_questions': recent_questions,
        'all_domains': all_domains,
        'all_skills': all_skills,
        'all_providers': all_providers,
        # Filter values for preserving state
        'subject_filter': subject_filter,
        'question_type_filter': question_type_filter,
        'difficulty_filter': difficulty_filter,
        'domain_filter': domain_filter,
        'skill_filter': skill_filter,
        'provider_filter': provider_filter,
        'is_active_filter': is_active_filter,
    }
    
    return render(request, 'admin/question_dashboard.html', context)
