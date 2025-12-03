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

from .models import Question, PracticeSession, UserAnswer, MarkedQuestion


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
    marked_for_review_only = request.GET.get('marked_review', False)
    
    # Base queryset - only active questions
    questions = Question.objects.filter(is_active=True)
    
    # Filter by marked for review if selected
    if marked_for_review_only:
        marked_question_ids = MarkedQuestion.objects.filter(
            user=request.user
        ).values_list('question_id', flat=True)
        questions = questions.filter(id__in=marked_question_ids)
    
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
    
    # Get count of marked questions for the user
    marked_count = MarkedQuestion.objects.filter(user=request.user).count()
    
    # Get last active session for this user
    last_session = PracticeSession.objects.filter(
        user=request.user,
        status='active'
    ).order_by('-started_at').first()
    
    # If there's an active session, get additional details
    if last_session:
        # Count answered questions in this session
        answered_count = UserAnswer.objects.filter(session=last_session).count()
        last_session.answered_count = answered_count
        
        # Get domain and skill names
        if last_session.domain_code:
            domain = Question.objects.filter(domain_code=last_session.domain_code).first()
            if domain:
                last_session.domain_name = domain.domain_name
        
        if last_session.skill_code:
            skill = Question.objects.filter(skill_code=last_session.skill_code).first()
            if skill:
                last_session.skill_name = skill.skill_name
    
    context = {
        'domains': domains,
        'skills_by_domain': skills_by_domain,
        'providers': list(all_providers),
        'total_questions': questions.count(),
        'subject': subject,
        'selected_providers': selected_providers,
        'selected_status': selected_status,
        'selected_difficulty': selected_difficulty,
        'marked_for_review_only': marked_for_review_only,
        'marked_count': marked_count,
        'last_session': last_session,
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
    - session: Resume existing session by ID
    - question: Start from specific question by ID
    
    Multiple filters can be combined (e.g., ?domain=CAS&skill=CTC)
    """
    # Get URL parameters
    domain_filter = request.GET.get('domain')
    skill_filter = request.GET.get('skill')
    provider_filter = request.GET.get('provider')
    question_type_filter = request.GET.get('type')
    session_id_param = request.GET.get('session')
    question_id_param = request.GET.get('question')
    mistakes_mode = request.GET.get('mistakes') == 'true'
    retry_mode = request.GET.get('retry') == 'true'
    date_range = request.GET.get('date_range', 'all')
    
    # Check if resuming an existing session
    session = None
    if session_id_param:
        try:
            session = PracticeSession.objects.get(
                id=session_id_param,
                user=request.user,
                status='active'
            )
            # Use session's filters if resuming
            domain_filter = session.domain_code or domain_filter
            skill_filter = session.skill_code or skill_filter
            provider_filter = session.provider_code or provider_filter
        except PracticeSession.DoesNotExist:
            # Session not found, will create new one
            session = None
    
    # Build query
    questions = Question.objects.filter(is_active=True)
    
    # Mistakes mode - only show questions the user got wrong
    if mistakes_mode or retry_mode:
        from datetime import timedelta
        
        # Get incorrect answers for this user
        mistake_query = UserAnswer.objects.filter(
            user=request.user,
            is_correct=False
        )
        
        # Apply date range filter for mistakes
        if date_range != 'all':
            date_filters = {
                'week': 7,
                'month': 30,
                '3months': 90
            }
            days = date_filters.get(date_range, 0)
            if days:
                cutoff_date = timezone.now() - timedelta(days=days)
                mistake_query = mistake_query.filter(answered_at__gte=cutoff_date)
        
        # Apply domain/skill filters to mistakes
        if domain_filter:
            mistake_query = mistake_query.filter(question__domain_code=domain_filter)
        if skill_filter:
            mistake_query = mistake_query.filter(question__skill_code=skill_filter)
        
        # Get question IDs from mistakes
        mistake_question_ids = mistake_query.values_list('question_id', flat=True).distinct()
        questions = questions.filter(id__in=mistake_question_ids)
    else:
        # Normal practice mode - apply filters from URL parameters
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
    
    # Get all questions for navigation (IDs only)
    question_ids = list(questions.values_list('id', flat=True))
    
    # Determine starting question
    first_question = None
    current_index = 1
    
    if question_id_param and question_id_param in [str(qid) for qid in question_ids]:
        # Start from specified question
        first_question = questions.filter(id=question_id_param).first()
        if first_question:
            current_index = question_ids.index(first_question.id) + 1
    else:
        # Start from first question
        first_question = questions.first() if total_questions > 0 else None
    
    # Create or reuse session
    if not session:
        # Generate unique session key with UUID for uniqueness
        session_key = f"session_{uuid.uuid4().hex[:12]}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
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
    else:
        session_key = session.session_key
    
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
        'current_index': current_index,
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


@login_required
@require_http_methods(["POST"])
def end_practice(request):
    """End practice session and return session ID for results."""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'Session ID required'
            }, status=400)
        
        # Get session
        session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
        
        # Update session status
        session.status = 'completed'
        session.completed_at = timezone.now()
        
        # Calculate total time
        if session.started_at:
            time_diff = session.completed_at - session.started_at
            session.time_spent_seconds = int(time_diff.total_seconds())
        
        # Calculate stats
        answers = UserAnswer.objects.filter(session=session)
        session.total_questions = answers.count()
        session.correct_answers = answers.filter(is_correct=True).count()
        
        session.save()
        
        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'redirect_url': f'/practice/results/{session.id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def practice_results(request, session_id):
    """Display detailed practice session results."""
    from django.db.models import Avg
    
    session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
    
    # Get all answers for this session
    answers = UserAnswer.objects.filter(session=session).select_related('question').order_by('answered_at')
    
    # Calculate statistics
    total_questions = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    incorrect_answers = total_questions - correct_answers
    accuracy = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Calculate average time per question
    avg_time = answers.aggregate(Avg('time_taken_seconds'))['time_taken_seconds__avg'] or 0
    
    context = {
        'session': session,
        'answers': answers,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'accuracy': round(accuracy, 1),
        'avg_time': round(avg_time, 1),
    }
    
    return render(request, 'practice/results.html', context)


@login_required
@require_http_methods(["POST"])
def mark_question_for_review(request):
    """
    Toggle mark for review on a question.
    
    POST /practice/api/mark-question/
    Body: { question_id: "uuid" }
    Returns: { marked: true/false }
    """
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        
        if not question_id:
            return JsonResponse({'error': 'Question ID is required'}, status=400)
        
        question = get_object_or_404(Question, id=question_id)
        
        # Check if already marked
        marked_question = MarkedQuestion.objects.filter(
            user=request.user,
            question=question
        ).first()
        
        if marked_question:
            # Unmark - remove from database
            marked_question.delete()
            return JsonResponse({'marked': False})
        else:
            # Mark - add to database
            MarkedQuestion.objects.create(
                user=request.user,
                question=question
            )
            return JsonResponse({'marked': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_marked_questions(request):
    """
    Get list of question IDs that are marked for review by the current user.
    
    GET /practice/api/marked-questions/
    Returns: { marked_question_ids: ["uuid1", "uuid2", ...] }
    """
    try:
        marked_questions = MarkedQuestion.objects.filter(
            user=request.user
        ).values_list('question_id', flat=True)
        
        return JsonResponse({
            'marked_question_ids': list(marked_questions)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_session_answers(request, session_id):
    """
    Get all answers for a specific practice session.
    
    GET /practice/api/session-answers/<session_id>/
    Returns: { 
        answers: {
            "question_id": {"answer": "A", "is_correct": true},
            ...
        }
    }
    """
    try:
        session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
        
        # Get all answers for this session
        answers = UserAnswer.objects.filter(session=session).select_related('question')
        
        # Build response dict
        answers_dict = {}
        for answer in answers:
            answers_dict[str(answer.question.id)] = {
                'answer': answer.user_answer,
                'is_correct': answer.is_correct,
                'time_taken': answer.time_taken_seconds,
            }
        
        return JsonResponse({
            'answers': answers_dict
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def resume_session(request, session_id):
    """
    Resume a previous practice session.
    
    GET /practice/resume/<session_id>/
    Redirects to practice interface with the session's questions and last answered position.
    """
    # Get the session
    session = get_object_or_404(PracticeSession, id=session_id, user=request.user)
    
    # Get all answered questions in this session to find the last one
    last_answer = UserAnswer.objects.filter(session=session).order_by('-answered_at').first()
    
    # Build the practice URL with session ID and filters
    params = {'session': str(session.id)}
    
    if session.domain_code:
        params['domain'] = session.domain_code
    if session.skill_code:
        params['skill'] = session.skill_code
    if session.provider_code:
        params['provider'] = session.provider_code
    
    # If there was a last answered question, start from the NEXT question
    # (since they already answered the last one)
    if last_answer:
        # Get the question after the last answered one
        questions = Question.objects.filter(is_active=True)
        if session.domain_code:
            questions = questions.filter(domain_code=session.domain_code)
        if session.skill_code:
            questions = questions.filter(skill_code=session.skill_code)
        if session.provider_code:
            questions = questions.filter(provider_code=session.provider_code)
        
        question_ids = list(questions.values_list('id', flat=True))
        try:
            last_index = question_ids.index(last_answer.question.id)
            # Get next question if available
            if last_index + 1 < len(question_ids):
                next_question_id = question_ids[last_index + 1]
                params['question'] = str(next_question_id)
        except ValueError:
            # Last answered question not in current filtered list
            pass
    
    # Build query string
    from urllib.parse import urlencode
    query_string = urlencode(params)
    
    # Redirect to practice interface with session context
    from django.shortcuts import redirect
    return redirect(f"/practice/?{query_string}")


@login_required
def mistake_log_view(request):
    """
    Mistake Log - shows all incorrect answers from practice sessions.
    
    GET /practice/mistake-log/
    Supports filters: domain, skill, date_range, sort
    """
    from datetime import datetime, timedelta
    from django.db.models import F, Prefetch
    
    # Get filter parameters
    domain_filter = request.GET.get('domain', '')
    skill_filter = request.GET.get('skill', '')
    date_range = request.GET.get('date_range', 'all')  # all, week, month, 3months
    sort_by = request.GET.get('sort', 'recent')  # recent, oldest, domain, skill
    
    # Base query - all incorrect answers for this user
    mistakes = UserAnswer.objects.filter(
        user=request.user,
        is_correct=False
    ).select_related(
        'question',
        'session'
    ).order_by('-answered_at')
    
    # Apply domain filter
    if domain_filter:
        mistakes = mistakes.filter(question__domain_code=domain_filter)
    
    # Apply skill filter
    if skill_filter:
        mistakes = mistakes.filter(question__skill_code=skill_filter)
    
    # Apply date range filter
    if date_range != 'all':
        date_filters = {
            'week': 7,
            'month': 30,
            '3months': 90
        }
        days = date_filters.get(date_range, 0)
        if days:
            cutoff_date = timezone.now() - timedelta(days=days)
            mistakes = mistakes.filter(answered_at__gte=cutoff_date)
    
    # Apply sorting
    if sort_by == 'oldest':
        mistakes = mistakes.order_by('answered_at')
    elif sort_by == 'domain':
        mistakes = mistakes.order_by('question__domain_name', '-answered_at')
    elif sort_by == 'skill':
        mistakes = mistakes.order_by('question__skill_name', '-answered_at')
    else:  # recent
        mistakes = mistakes.order_by('-answered_at')
    
    # Pagination
    paginator = Paginator(mistakes, 20)  # 20 mistakes per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    total_mistakes = mistakes.count()
    
    # Group mistakes by domain
    domain_stats = mistakes.values(
        'question__domain_code',
        'question__domain_name'
    ).annotate(
        mistake_count=Count('id')
    ).order_by('-mistake_count')
    
    # Group mistakes by skill
    skill_stats = mistakes.values(
        'question__skill_code',
        'question__skill_name',
        'question__domain_code'
    ).annotate(
        mistake_count=Count('id')
    ).order_by('-mistake_count')[:10]  # Top 10 skills with most mistakes
    
    # Get all unique domains for filter dropdown
    all_domains = Question.objects.values(
        'domain_code',
        'domain_name'
    ).distinct().order_by('domain_name')
    
    # Get skills for selected domain (for filter dropdown)
    domain_skills = []
    if domain_filter:
        domain_skills = Question.objects.filter(
            domain_code=domain_filter
        ).values(
            'skill_code',
            'skill_name'
        ).distinct().order_by('skill_name')
    
    context = {
        'page_obj': page_obj,
        'total_mistakes': total_mistakes,
        'domain_stats': domain_stats,
        'skill_stats': skill_stats,
        'all_domains': all_domains,
        'domain_skills': domain_skills,
        'selected_domain': domain_filter,
        'selected_skill': skill_filter,
        'selected_date_range': date_range,
        'selected_sort': sort_by,
    }
    
    return render(request, 'practice/mistake_log.html', context)
