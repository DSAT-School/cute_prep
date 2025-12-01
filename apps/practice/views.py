"""
Practice app views.

Handles practice modules/filter page and practice session interface.
"""
import json
import uuid
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Question, PracticeSession, UserAnswer


@login_required
def practice_modules_view(request):
    """
    Practice modules/filter page showing domains and skills.
    URL: /practice/modules/
    Supports filters: subject, provider, status, difficulty
    """
    # Get filter parameters from URL
    subject = request.GET.get('subject', 'reading')  # reading or math
    selected_providers = request.GET.getlist('provider')
    selected_status = request.GET.getlist('status')
    selected_difficulty = request.GET.getlist('difficulty')
    
    # Base queryset - only active questions
    questions = Question.objects.filter(is_active=True)
    
    # Filter by subject (Reading & Writing vs Math)
    if subject == 'reading':
        # Reading & Writing domains: CAS, INI, EOI, SEC
        reading_domains = ['CAS', 'INI', 'EOI', 'SEC']
        questions = questions.filter(domain_code__in=reading_domains)
    else:
        # Math domains: H, P, Q, S
        math_domains = ['H', 'P', 'Q', 'S']
        questions = questions.filter(domain_code__in=math_domains)
    
    # Filter by providers if selected
    if selected_providers:
        questions = questions.filter(provider_code__in=selected_providers)
    
    # Note: Status and Difficulty filters require user progress tracking
    # which we can implement later with a UserProgress model
    
    # Get all domains with question counts (filtered)
    domains = questions.values(
        'domain_code', 'domain_name'
    ).annotate(
        question_count=Count('id')
    ).order_by('domain_name')
    
    # Get all skills grouped by domain with question counts (filtered)
    skills_by_domain = {}
    for domain in domains:
        skills = questions.filter(
            domain_code=domain['domain_code']
        ).values(
            'skill_code', 'skill_name'
        ).annotate(
            question_count=Count('id')
        ).order_by('skill_name')
        
        skills_by_domain[domain['domain_code']] = list(skills)
    
    # Get all providers for filter options (unfiltered for checkbox list)
    all_providers = Question.objects.values(
        'provider_code', 'provider_name'
    ).annotate(
        question_count=Count('id')
    ).distinct().order_by('provider_name')
    
    context = {
        'domains': domains,
        'skills_by_domain': skills_by_domain,
        'providers': list(all_providers),
        'total_questions': questions.count(),
        'subject': subject,
        'selected_providers': selected_providers,
        'selected_status': selected_status,
        'selected_difficulty': selected_difficulty,
    }
    
    return render(request, 'practice/modules.html', context)


@login_required
def practice_view(request):
    """
    Main practice interface with URL parameter filtering.
    
    Supported URL parameters:
    - domain: Filter by domain_code (e.g., ?domain=CAS)
    - skill: Filter by skill_code (e.g., ?skill=CTC)
    - provider: Filter by provider_code (e.g., ?provider=cb)
    - difficulty: Filter by difficulty level
    - type: Filter by question_type (e.g., ?type=mcq)
    
    Multiple filters can be combined (e.g., ?domain=CAS&skill=CTC)
    """
    # Get URL parameters
    domain_filter = request.GET.get('domain')
    skill_filter = request.GET.get('skill')
    provider_filter = request.GET.get('provider')
    question_type_filter = request.GET.get('type')
    
    # Build query
    questions = Question.objects.filter(is_active=True)
    
    # Apply filters from URL parameters
    if domain_filter:
        questions = questions.filter(domain_code=domain_filter)
    
    if skill_filter:
        questions = questions.filter(skill_code=skill_filter)
    
    if provider_filter:
        questions = questions.filter(provider_code=provider_filter)
    
    if question_type_filter:
        questions = questions.filter(question_type=question_type_filter)
    
    # Get total count
    total_questions = questions.count()
    
    # Get first question for initial display
    first_question = questions.first() if total_questions > 0 else None
    
    # Get all questions for navigation (IDs only)
    question_ids = list(questions.values_list('id', flat=True))
    
    # Create or get practice session
    # Generate unique session key based on filters
    session_key_parts = [
        f"user_{request.user.id}",
        f"domain_{domain_filter or 'all'}",
        f"skill_{skill_filter or 'all'}",
        f"provider_{provider_filter or 'all'}",
        timezone.now().strftime("%Y%m%d%H%M%S")
    ]
    session_key = "_".join(session_key_parts)
    
    # Create new session
    session = PracticeSession.objects.create(
        user=request.user,
        session_key=session_key,
        status='active',
        domain_code=domain_filter or '',
        skill_code=skill_filter or '',
        provider_code=provider_filter or '',
        total_questions=total_questions
    )
    
    # Prepare filter context
    filter_context = {
        'domain': domain_filter,
        'skill': skill_filter,
        'provider': provider_filter,
        'type': question_type_filter,
    }
    
    context = {
        'total_questions': total_questions,
        'first_question': first_question,
        'question_ids': json.dumps([str(qid) for qid in question_ids]),
        'filters': filter_context,
        'current_index': 1 if first_question else 0,
        'session_id': str(session.id),
        'session_key': session_key,
    }
    
    return render(request, 'practice/practice.html', context)


@login_required
@require_http_methods(["GET"])
def get_question(request, question_id):
    """
    API endpoint to get a specific question by ID.
    
    Returns JSON with question data.
    """
    question = get_object_or_404(Question, id=question_id, is_active=True)
    
    data = {
        'id': str(question.id),
        'identifier_id': question.identifier_id,
        'question_id': str(question.question_id),
        'domain_name': question.domain_name,
        'domain_code': question.domain_code,
        'skill_name': question.skill_name,
        'skill_code': question.skill_code,
        'provider_name': question.provider_name,
        'question_type': question.question_type,
        'stimulus': question.stimulus or '',
        'stem': question.stem,
        'explanation': question.explanation,
        'mcq_answer': question.mcq_answer,
        'mcq_options': question.mcq_option_list or {},
        'tutorial_link': question.tutorial_link,
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def check_answer(request, question_id):
    """
    API endpoint to check if a user's answer is correct.
    
    Expected POST data:
    - answer: User's selected answer (A, B, C, D)
    - session_id: Practice session UUID
    - time_taken: Time taken in seconds
    
    Returns JSON with correctness, correct answer, and explanation.
    Saves the answer to database for tracking.
    """
    try:
        data = json.loads(request.body)
        user_answer = data.get('answer', '').strip().upper()
        session_id = data.get('session_id')
        time_taken = data.get('time_taken', 0)
        
        question = get_object_or_404(Question, id=question_id, is_active=True)
        
        # Check if answer is correct
        is_correct = user_answer == question.mcq_answer.upper()
        
        # Save answer to database if session_id is provided
        if session_id:
            try:
                session = PracticeSession.objects.get(id=session_id, user=request.user)
                
                # Check if answer already exists (prevent duplicates)
                answer, created = UserAnswer.objects.get_or_create(
                    session=session,
                    question=question,
                    defaults={
                        'user': request.user,
                        'user_answer': user_answer,
                        'correct_answer': question.mcq_answer,
                        'is_correct': is_correct,
                        'time_taken_seconds': int(time_taken),
                    }
                )
                
                # Update session statistics
                if created:
                    session.questions_answered += 1
                    if is_correct:
                        session.correct_answers += 1
                    session.total_time_seconds += int(time_taken)
                    session.save()
                    
            except PracticeSession.DoesNotExist:
                pass  # Session not found, continue without saving
        
        response_data = {
            'is_correct': is_correct,
            'correct_answer': question.mcq_answer,
            'explanation': question.explanation,
            'tutorial_link': question.tutorial_link,
            'time_taken': time_taken,
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def submit_answer(request):
    """
    API endpoint to submit an answer.
    
    Expected POST data:
    - question_id: UUID of the question
    - answer: User's answer
    
    Returns JSON with correctness and explanation.
    """
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        user_answer = data.get('answer', '').strip().upper()
        
        question = get_object_or_404(Question, id=question_id, is_active=True)
        
        # Check if answer is correct
        is_correct = user_answer == question.mcq_answer.upper()
        
        response_data = {
            'is_correct': is_correct,
            'correct_answer': question.mcq_answer,
            'explanation': question.explanation,
            'tutorial_link': question.tutorial_link,
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
