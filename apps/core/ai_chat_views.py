"""
AI Chat views for SAT Buddy feature.
"""
import json
import os
import uuid
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.cache import cache
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)


@login_required
def ai_chat_view(request):
    """
    Main AI chat interface (SAT Buddy).
    """
    context = {
        'page_title': 'SAT Buddy',
    }
    return render(request, 'ai_chat/chat.html', context)


@login_required
@require_http_methods(["POST"])
def ai_chat_message(request):
    """
    Handle AI chat messages using Google Gemini with async Celery processing.
    
    POST /ai/chat/message/
    Expected: { message: "user message", context: "optional context", images: ["image_id1", ...] }
    Returns: { task_id: "unique_id", success: true } for polling
    """
    from apps.core.tasks import process_ai_chat_message
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        context_info = data.get('context', '')
        image_ids = data.get('images', [])
        conversation_history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Check if Celery is available
        celery_available = False
        try:
            from celery import current_app
            # Try to inspect Celery to see if workers are running
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            celery_available = stats is not None and len(stats) > 0
        except Exception as e:
            logger.info(f"Celery not available: {e}")
            celery_available = False
        
        if celery_available:
            # Initialize cache with processing status
            cache.set(f'ai_task_{task_id}', {
                'status': 'processing',
                'success': True
            }, timeout=3600)
            
            # Queue async task
            process_ai_chat_message.delay(
                task_id=task_id,
                user_message=user_message,
                context_info=context_info,
                image_ids=image_ids,
                conversation_history=conversation_history,
                user_id=request.user.id
            )
            logger.info(f"Task {task_id} queued for async processing")
        else:
            # Process synchronously
            logger.info(f"Processing task {task_id} synchronously (Celery unavailable)")
            cache.set(f'ai_task_{task_id}', {
                'status': 'processing',
                'success': True
            }, timeout=3600)
            
            try:
                # Call the task function directly (synchronously)
                from apps.core.tasks import process_ai_chat_message as sync_task
                sync_task(
                    task_id=task_id,
                    user_message=user_message,
                    context_info=context_info,
                    image_ids=image_ids,
                    conversation_history=conversation_history,
                    user_id=request.user.id
                )
            except Exception as sync_error:
                logger.error(f"Sync processing failed: {sync_error}")
                cache.set(f'ai_task_{task_id}', {
                    'status': 'failed',
                    'success': False,
                    'error': f'Processing failed: {str(sync_error)}'
                }, timeout=3600)
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'status': 'processing'
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.exception(f"Unexpected error in ai_chat_message: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error communicating with AI: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ai_task_status(request, task_id):
    """
    Poll for AI task status and result.
    
    GET /ai/task/<task_id>/
    Returns: { status: "processing|completed|failed", response: "...", success: true }
    """
    try:
        # Check cache for task result
        result = cache.get(f'ai_task_{task_id}')
        
        if result is None:
            return JsonResponse({
                'success': False,
                'status': 'not_found',
                'error': 'Task not found or expired'
            }, status=404)
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.exception(f"Error checking task status: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_upload_image(request):
    """
    Handle image uploads for AI analysis.
    
    POST /ai/upload-image/
    """
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No image provided'
            }, status=400)
        
        image = request.FILES['image']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if image.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Only JPG, PNG, and GIF are allowed.'
            }, status=400)
        
        # Validate file size (max 5MB)
        if image.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File size too large. Maximum 5MB allowed.'
            }, status=400)
        
        # Save file
        file_path = f'ai_uploads/{request.user.id}/{image.name}'
        saved_path = default_storage.save(file_path, ContentFile(image.read()))
        file_url = default_storage.url(saved_path)
        
        return JsonResponse({
            'success': True,
            'file_url': file_url,
            'file_path': saved_path,
            'message': 'Image uploaded successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def ai_generate_question(request):
    """
    Generate a practice question asynchronously using Google Gemini.
    
    POST /ai/generate-question/
    Expected: { topic: "topic name", difficulty: "easy/medium/hard" }
    Returns: { task_id: "unique_id", success: true } for polling
    """
    from apps.core.tasks import process_ai_question_generation
    
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'medium')
        
        if not topic:
            return JsonResponse({
                'success': False,
                'error': 'Topic is required'
            }, status=400)
        
        # Check if API key is configured
        if not settings.GEMINI_API_KEY:
            return JsonResponse({
                'success': False,
                'error': 'Gemini API key not configured.'
            }, status=500)
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Check if Celery is available
        celery_available = False
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            celery_available = stats is not None and len(stats) > 0
        except Exception as e:
            logger.info(f"Celery not available for question generation: {e}")
            celery_available = False
        
        if celery_available:
            # Initialize cache with processing status
            cache.set(f'ai_task_{task_id}', {
                'status': 'processing',
                'success': True
            }, timeout=3600)
            
            # Queue async task
            process_ai_question_generation.delay(
                task_id=task_id,
                topic=topic,
                difficulty=difficulty
            )
            logger.info(f"Question generation task {task_id} queued for async processing")
        else:
            # Process synchronously
            logger.info(f"Processing question generation task {task_id} synchronously (Celery unavailable)")
            cache.set(f'ai_task_{task_id}', {
                'status': 'processing',
                'success': True
            }, timeout=3600)
            
            try:
                from apps.core.tasks import process_ai_question_generation as sync_task
                sync_task(
                    task_id=task_id,
                    topic=topic,
                    difficulty=difficulty
                )
            except Exception as sync_error:
                logger.error(f"Sync question generation failed: {sync_error}")
                cache.set(f'ai_task_{task_id}', {
                    'status': 'failed',
                    'success': False,
                    'error': f'Question generation failed: {str(sync_error)}'
                }, timeout=3600)
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'status': 'processing'
        })
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to parse AI response: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error generating question: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def ai_chat_history(request):
    """
    Get user's chat history with AI.
    
    GET /ai/chat/history/
    """
    try:
        # TODO: Implement actual chat history storage and retrieval
        # For now, returning empty history
        
        return JsonResponse({
            'success': True,
            'history': []
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
