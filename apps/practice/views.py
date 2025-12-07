"""
Practice app views.

Handles practice modules/filter page and practice session interface.
"""
import json
import uuid
from fractions import Fraction
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Question, PracticeSession, UserAnswer, MarkedQuestion, MasteredQuestion


def check_spr_answer(user_answer, correct_answers):
    """
    Check if SPR (Student Produced Response) answer is correct.
    Handles various formats: integers, decimals, fractions.
    
    Args:
        user_answer: String answer from user
        correct_answers: List of acceptable correct answers or single string
    
    Returns:
        Boolean indicating if answer is correct
    """
    try:
        # Ensure correct_answers is a list
        if isinstance(correct_answers, str):
            correct_answers = [correct_answers]
        elif not correct_answers:
            return False
        
        # Remove whitespace from user answer
        user_answer = user_answer.strip()
        
        # Helper function to convert answer to decimal
        def to_decimal(ans):
            ans = ans.strip()
            # Handle fractions (e.g., "1/2", "3/4")
            if '/' in ans:
                frac = Fraction(ans)
                return float(frac)
            # Handle decimals and integers
            else:
                return float(ans)
        
        # Convert user answer to decimal
        user_value = to_decimal(user_answer)
        
        # Check against all acceptable answers
        tolerance = 0.0001
        for correct_answer in correct_answers:
            correct_value = to_decimal(correct_answer)
            if abs(user_value - correct_value) < tolerance:
                return True
        
        return False
        
    except (ValueError, ZeroDivisionError, InvalidOperation):
        # If conversion fails, do string comparison as fallback
        user_answer_lower = user_answer.lower()
        return any(user_answer_lower == ans.strip().lower() for ans in correct_answers)


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
    
    # Filter by status if selected
    if selected_status:
        if 'mastered' in selected_status:
            # Only mastered questions
            mastered_question_ids = MasteredQuestion.objects.filter(
                user=request.user
            ).values_list('question_id', flat=True)
            questions = questions.filter(id__in=mastered_question_ids)
        elif 'not_mastered' in selected_status:
            # Only non-mastered questions
            mastered_question_ids = MasteredQuestion.objects.filter(
                user=request.user
            ).values_list('question_id', flat=True)
            questions = questions.exclude(id__in=mastered_question_ids)
    
    # Note: Difficulty filters can be implemented when difficulty data is added to questions
    
    # Get all domains with question counts (filtered)
    domains = questions.values(
        'domain_code', 'domain_name'
    ).annotate(
        question_count=Count('id')
    ).order_by('domain_name')
    
    # Get all skills grouped by domain with question counts and statistics (filtered)
    from django.db.models import Avg, Q
    
    skills_by_domain = {}
    for domain in domains:
        skills = questions.filter(
            domain_code=domain['domain_code']
        ).values(
            'skill_code', 'skill_name'
        ).annotate(
            question_count=Count('id')
        ).order_by('skill_name')
        
        # Calculate statistics for each skill
        skills_list = []
        for skill in skills:
            # Get all user answers for this skill
            user_answers = UserAnswer.objects.filter(
                user=request.user,
                question__skill_code=skill['skill_code']
            )
            
            total_attempted = user_answers.count()
            correct_answers = user_answers.filter(is_correct=True).count()
            
            # Get mastered questions count for this skill
            mastered_count = MasteredQuestion.objects.filter(
                user=request.user,
                question__skill_code=skill['skill_code']
            ).count()
            
            # Calculate accuracy and progress
            if total_attempted > 0:
                accuracy = round((correct_answers / total_attempted) * 100, 1)
            else:
                accuracy = 0
            
            # Progress is based on mastered questions
            if skill['question_count'] > 0:
                progress = min(round((mastered_count / skill['question_count']) * 100), 100)
            else:
                progress = 0
            
            # Get last active session for this specific skill
            last_skill_session = PracticeSession.objects.filter(
                user=request.user,
                skill_code=skill['skill_code'],
                status='active'
            ).order_by('-started_at').first()
            
            last_question_id = None
            if last_skill_session:
                # Get the last answered question in this session
                last_answer = UserAnswer.objects.filter(
                    session=last_skill_session
                ).order_by('-answered_at').first()
                
                if last_answer:
                    last_question_id = str(last_answer.question_id)
            
            skill_dict = dict(skill)
            skill_dict['total_attempted'] = total_attempted
            skill_dict['correct_answers'] = correct_answers
            skill_dict['mastered_count'] = mastered_count
            skill_dict['accuracy'] = accuracy
            skill_dict['progress'] = progress
            skill_dict['last_session'] = last_skill_session
            skill_dict['last_question_id'] = last_question_id
            
            skills_list.append(skill_dict)
        
        skills_by_domain[domain['domain_code']] = skills_list
    
    # Get all providers for filter options (unfiltered for checkbox list)
    all_providers = Question.objects.values(
        'provider_code', 'provider_name'
    ).annotate(
        question_count=Count('id')
    ).distinct().order_by('provider_name')
    
    # Get count of marked questions for the user
    marked_count = MarkedQuestion.objects.filter(user=request.user).count()
    
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
    question_id_param = request.GET.get('question')
    resume_from_param = request.GET.get('resume_from')  # For resuming from specific question
    mistakes_mode = request.GET.get('mistakes') == 'true'
    retry_mode = request.GET.get('retry') == 'true'
    date_range = request.GET.get('date_range', 'all')
    
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
    
    # Handle resume mode with custom question ordering
    resume_mode = request.GET.get('resume') == 'true'
    question_ids = []
    resume_start_index = 0  # Track where to start in resume mode
    
    if resume_mode and skill_filter:
        # Custom ordering for resume: mastered -> fresh -> attempted (wrong)
        
        # Get all question IDs for this skill (in database order)
        all_skill_question_ids = list(questions.values_list('id', flat=True))
        
        # Step 1: Get mastered questions for this skill (preserve order)
        mastered_question_objs = MasteredQuestion.objects.filter(
            user=request.user,
            question__skill_code=skill_filter,
            question__is_active=True
        ).select_related('question')
        
        mastered_question_ids = []
        mastered_set = set()
        for mq in mastered_question_objs:
            if mq.question_id not in mastered_set:
                mastered_question_ids.append(mq.question_id)
                mastered_set.add(mq.question_id)
        
        # Step 2: Get all attempted questions (not mastered)
        attempted_question_objs = UserAnswer.objects.filter(
            user=request.user,
            question__skill_code=skill_filter
        ).values_list('question_id', flat=True).distinct()
        
        attempted_not_mastered_ids = []
        attempted_set = set()
        for qid in attempted_question_objs:
            if qid not in mastered_set and qid not in attempted_set:
                attempted_not_mastered_ids.append(qid)
                attempted_set.add(qid)
        
        # Step 3: Get fresh questions (never attempted, not mastered)
        all_processed_set = mastered_set | attempted_set
        fresh_question_ids = []
        for qid in all_skill_question_ids:
            if qid not in all_processed_set:
                fresh_question_ids.append(qid)
        
        # Build the ordered list: mastered -> fresh -> attempted
        question_ids = mastered_question_ids + fresh_question_ids + attempted_not_mastered_ids
        
        # Set resume start index to first fresh question (right after mastered)
        # Only if we have fresh questions and no specific question requested
        if not question_id_param and len(mastered_question_ids) < len(question_ids):
            resume_start_index = len(mastered_question_ids)
    else:
        # Normal mode: get questions in default order
        question_ids = list(questions.values_list('id', flat=True))
    
    # Determine starting question and index
    first_question = None
    current_index = 0  # JavaScript uses 0-based indexing
    
    # Priority: question parameter > resume start index > first question
    question_param = question_id_param or resume_from_param
    
    if question_param and question_ids:
        # Try to find and start from the specified question
        try:
            question_uuid = uuid.UUID(question_param)
            # Convert question_ids to set for faster lookup
            question_ids_set = set(question_ids)
            if question_uuid in question_ids_set:
                first_question = Question.objects.filter(id=question_uuid).first()
                if first_question:
                    current_index = question_ids.index(question_uuid)
            else:
                # Question not in filtered list - this might happen if:
                # 1. Question doesn't match current filters (domain/skill)
                # 2. Question is not active
                # Try to add it to the list if it matches filters
                question_obj = Question.objects.filter(id=question_uuid, is_active=True).first()
                if question_obj:
                    # Check if question matches the filters
                    matches_filter = True
                    if skill_filter and question_obj.skill_code != skill_filter:
                        matches_filter = False
                    if domain_filter and question_obj.domain_code != domain_filter:
                        matches_filter = False
                    
                    if matches_filter:
                        # Add question to the list at the beginning
                        question_ids.insert(0, question_uuid)
                        first_question = question_obj
                        current_index = 0
                    else:
                        # Question doesn't match filters, start from first
                        first_question = Question.objects.filter(id=question_ids[0]).first() if question_ids else None
                        current_index = 0
                else:
                    # Question doesn't exist or not active, start from first
                    first_question = Question.objects.filter(id=question_ids[0]).first() if question_ids else None
                    current_index = 0
        except (ValueError, AttributeError):
            # Invalid UUID, start from first
            first_question = Question.objects.filter(id=question_ids[0]).first() if question_ids else None
            current_index = 0
    elif question_ids:
        # No question parameter - use resume start index if in resume mode
        if resume_mode and resume_start_index > 0 and resume_start_index < len(question_ids):
            current_index = resume_start_index
            first_question = Question.objects.filter(id=question_ids[resume_start_index]).first()
        else:
            # Start from first question
            current_index = 0
            first_question = Question.objects.filter(id=question_ids[0]).first()
    else:
        # No questions available
        first_question = None
    
    # Create new session
    # Generate unique session key with UUID for uniqueness
    session_key = f"session_{uuid.uuid4().hex[:12]}_{timezone.now().strftime('%Y%m%d%H%M%S')}"
    
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
        'initial_index': current_index,  # 0-based index for JavaScript
        'session_id': str(session.id),
        'session_key': session_key,
    }
    
    return render(request, 'practice/practice.html', context)


@login_required
@require_http_methods(["GET"])
def get_question(request, question_id):
    """
    API endpoint to get a specific question by ID.
    
    Returns JSON with question data including attempt history.
    """
    question = get_object_or_404(Question, id=question_id, is_active=True)
    
    # Get attempt history for this user and question
    user_attempts = UserAnswer.objects.filter(
        user=request.user,
        question=question
    ).order_by('-answered_at')
    
    attempt_count = user_attempts.count()
    last_attempt = user_attempts.first()
    
    last_attempt_data = None
    if last_attempt:
        last_attempt_data = {
            'answer': last_attempt.user_answer,
            'is_correct': last_attempt.is_correct,
            'answered_at': last_attempt.answered_at.isoformat(),
            'time_taken': last_attempt.time_taken_seconds
        }
    
    # Get all attempts history
    all_attempts_data = []
    for attempt in user_attempts:
        all_attempts_data.append({
            'answer': attempt.user_answer,
            'is_correct': attempt.is_correct,
            'answered_at': attempt.answered_at.isoformat(),
            'time_taken': attempt.time_taken_seconds,
            'session_id': str(attempt.session_id) if attempt.session_id else None
        })
    
    # Determine if user can toggle mastered status
    can_toggle_mastered = False
    is_auto_mastered = False
    
    if attempt_count > 0:
        first_attempt = user_attempts.order_by('answered_at').first()
        has_wrong_attempt = user_attempts.filter(is_correct=False).exists()
        has_correct_attempt = user_attempts.filter(is_correct=True).exists()
        
        # Auto-mastered if first attempt was correct
        if attempt_count == 1 and first_attempt.is_correct:
            is_auto_mastered = True
            can_toggle_mastered = True  # Can unmark
        # Can manually master if got wrong then correct
        elif has_wrong_attempt and has_correct_attempt:
            can_toggle_mastered = True
    
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
        'spr_answer': question.spr_answer,
        'tutorial_link': question.tutorial_link,
        'attempt_count': attempt_count,
        'last_attempt': last_attempt_data,
        'all_attempts': all_attempts_data,
        'can_toggle_mastered': can_toggle_mastered,
        'is_auto_mastered': is_auto_mastered,
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
        user_answer = data.get('answer', '').strip()
        session_id = data.get('session_id')
        time_taken = data.get('time_taken', 0)
        
        question = get_object_or_404(Question, id=question_id, is_active=True)
        
        # Check if answer is correct based on question type
        if question.question_type in ['spr', 'grid_in']:
            # For SPR questions, compare numerical values
            is_correct = check_spr_answer(user_answer, question.spr_answer or [])
            # Use first answer in list for display
            correct_answer = question.spr_answer[0] if question.spr_answer else ''
        else:
            # For MCQ questions, compare uppercase letters
            user_answer = user_answer.upper()
            is_correct = user_answer == question.mcq_answer.upper()
            correct_answer = question.mcq_answer
        
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
                        'correct_answer': correct_answer,
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
                    
                    # Mastered logic:
                    # 1. Auto-master if answered correctly on first attempt (across all sessions)
                    # 2. Don't auto-master if user already got it wrong before
                    if is_correct:
                        # Get all previous attempts for this question by this user
                        all_attempts = UserAnswer.objects.filter(
                            user=request.user,
                            question=question
                        ).order_by('answered_at')
                        
                        total_attempts = all_attempts.count()
                        
                        # If this is the first attempt ever and it's correct - auto-master
                        if total_attempts == 1:
                            from .models import MasteredQuestion
                            MasteredQuestion.objects.get_or_create(
                                user=request.user,
                                question=question
                            )
                    
            except PracticeSession.DoesNotExist:
                pass  # Session not found, continue without saving
        
        response_data = {
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': question.explanation,
            'tutorial_link': question.tutorial_link,
            'time_taken': time_taken,
            'question_type': question.question_type,
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
    from apps.core.services_delta import DeltaService
    
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
        
        # Award Delta coins for completing practice
        delta_earned = 0
        try:
            accuracy = (session.correct_answers / session.total_questions * 100) if session.total_questions > 0 else 0
            
            # Check if this is user's first practice session
            is_first_practice = PracticeSession.objects.filter(
                user=request.user,
                status='completed'
            ).count() == 1
            
            if is_first_practice:
                # First practice bonus
                tx = DeltaService.award_for_activity(
                    user=request.user,
                    activity_name='first_practice',
                    reference_id=str(session.id),
                    reference_type='practice_session'
                )
                if tx:
                    delta_earned += tx.amount
            
            # Perfect practice bonus (100% accuracy)
            if accuracy == 100:
                tx = DeltaService.award_for_activity(
                    user=request.user,
                    activity_name='perfect_practice',
                    reference_id=str(session.id),
                    reference_type='practice_session',
                    accuracy=accuracy
                )
                if tx:
                    delta_earned += tx.amount
            # High accuracy bonus (80%+)
            elif accuracy >= 80:
                tx = DeltaService.award_for_activity(
                    user=request.user,
                    activity_name='high_accuracy_practice',
                    reference_id=str(session.id),
                    reference_type='practice_session',
                    accuracy=accuracy
                )
                if tx:
                    delta_earned += tx.amount
            
            # Base reward for completing session
            tx = DeltaService.award_for_activity(
                user=request.user,
                activity_name='complete_practice_session',
                reference_id=str(session.id),
                reference_type='practice_session'
            )
            if tx:
                delta_earned += tx.amount
            
            # Award for each correct answer
            if session.correct_answers > 0:
                from decimal import Decimal
                tx = DeltaService.add_delta(
                    user=request.user,
                    amount=Decimal('5.00') * session.correct_answers,
                    transaction_type='earn',
                    description=f'Answered {session.correct_answers} questions correctly',
                    reference_id=str(session.id),
                    reference_type='correct_answers'
                )
                if tx:
                    delta_earned += tx.amount
        
        except Exception as delta_error:
            # Log Delta error but don't fail the session completion
            print(f"Delta award error: {delta_error}")
        
        return JsonResponse({
            'success': True,
            'session_id': str(session.id),
            'redirect_url': f'/practice/results/{session.id}/',
            'delta_earned': str(delta_earned) if delta_earned > 0 else None
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
@require_http_methods(["POST"])
def master_question(request):
    """
    Toggle mastered status on a question.
    
    Rules:
    1. Auto-mastered (first attempt correct): User can only UNMARK, not toggle
    2. Manual mastering: User must have wrong attempt followed by correct attempt in different session
    
    POST /practice/api/master-question/
    Body: { question_id: "uuid" }
    Returns: { mastered: true/false, error: "message", can_toggle: true/false }
    """
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        
        if not question_id:
            return JsonResponse({'error': 'Question ID is required'}, status=400)
        
        question = get_object_or_404(Question, id=question_id)
        
        # Get all attempts for this question
        all_attempts = UserAnswer.objects.filter(
            user=request.user,
            question=question
        ).order_by('answered_at')
        
        if not all_attempts.exists():
            return JsonResponse({
                'success': False,
                'mastered': False,
                'error': 'You must attempt this question before marking it as mastered.',
                'can_toggle': False
            }, status=400)
        
        # Check if already mastered
        mastered_question = MasteredQuestion.objects.filter(
            user=request.user,
            question=question
        ).first()
        
        # Check attempt history
        total_attempts = all_attempts.count()
        first_attempt = all_attempts.first()
        has_wrong_attempt = all_attempts.filter(is_correct=False).exists()
        has_correct_attempt = all_attempts.filter(is_correct=True).exists()
        
        # Determine if user can manually toggle mastered status
        can_manually_master = False
        
        # If first attempt was correct - it was auto-mastered, user can only unmark
        if total_attempts == 1 and first_attempt.is_correct:
            # Auto-mastered case - allow unmask only
            if mastered_question:
                mastered_question.delete()
                return JsonResponse({
                    'success': True,
                    'mastered': False,
                    'message': 'Question unmarked as mastered',
                    'can_toggle': True
                })
            else:
                return JsonResponse({
                    'success': False,
                    'mastered': False,
                    'error': 'This question was auto-mastered but record is missing.',
                    'can_toggle': False
                }, status=400)
        
        # User can manually master if: got it wrong before AND got it correct later
        if has_wrong_attempt and has_correct_attempt:
            can_manually_master = True
        
        if not can_manually_master:
            return JsonResponse({
                'success': False,
                'mastered': False,
                'error': 'You can only mark as mastered after getting it wrong first and then correct.',
                'can_toggle': False
            }, status=400)
        
        # Toggle mastered status
        if mastered_question:
            # Unmark mastered
            mastered_question.delete()
            return JsonResponse({
                'success': True,
                'mastered': False,
                'message': 'Question unmarked as mastered',
                'can_toggle': True
            })
        else:
            # Mark as mastered
            MasteredQuestion.objects.create(
                user=request.user,
                question=question
            )
            return JsonResponse({
                'success': True,
                'mastered': True,
                'message': 'Question marked as mastered',
                'can_toggle': True
            })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_mastered_questions(request):
    """
    Get list of question IDs that are mastered by the current user.
    
    GET /practice/api/mastered-questions/
    Returns: { mastered_question_ids: ["uuid1", "uuid2", ...] }
    """
    try:
        mastered_questions = MasteredQuestion.objects.filter(
            user=request.user
        ).values_list('question_id', flat=True)
        
        return JsonResponse({
            'mastered_question_ids': [str(qid) for qid in mastered_questions]
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
@require_http_methods(["POST"])
def get_attempted_questions(request):
    """
    Get attempt counts for a list of question IDs.
    
    POST /practice/api/attempted-questions/
    Body: { question_ids: ["uuid1", "uuid2", ...] }
    Returns: { 
        attempt_counts: {
            "question_id": 3,
            ...
        }
    }
    """
    try:
        data = json.loads(request.body)
        question_ids = data.get('question_ids', [])
        
        if not question_ids:
            return JsonResponse({'attempt_counts': {}})
        
        # Convert string UUIDs to UUID objects
        uuid_list = [uuid.UUID(qid) for qid in question_ids]
        
        # Get attempt counts for each question
        from django.db.models import Count
        attempt_data = UserAnswer.objects.filter(
            user=request.user,
            question_id__in=uuid_list
        ).values('question_id').annotate(
            count=Count('id')
        )
        
        # Build response dict
        attempt_counts = {}
        for item in attempt_data:
            attempt_counts[str(item['question_id'])] = item['count']
        
        return JsonResponse({
            'attempt_counts': attempt_counts
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
