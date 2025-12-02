"""
AI Chat views for Ask Prof. Coco feature.
"""
import json
import os
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)


@login_required
def ai_chat_view(request):
    """
    Main AI chat interface (Ask Prof. Coco).
    """
    context = {
        'page_title': 'Ask Prof. Coco',
    }
    return render(request, 'ai_chat/chat.html', context)


@login_required
@require_http_methods(["POST"])
def ai_chat_message(request):
    """
    Handle AI chat messages using Google Gemini.
    
    POST /ai/chat/message/
    Expected: { message: "user message", context: "optional context", images: ["image_id1", ...] }
    Returns: { response: "AI response", success: true }
    """
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
        
        # Check if API key is configured
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is not configured in settings")
            return JsonResponse({
                'success': False,
                'error': 'AI service is not configured. Please contact administrator.'
            }, status=500)
        
        # Configure Gemini
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-2.5-flash (latest stable model)
            model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as config_error:
            logger.error(f"Failed to configure Gemini: {config_error}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to initialize AI service: {str(config_error)}'
            }, status=500)
        
        # Build system prompt with SAT tutor context
        system_prompt = """You are Prof. Coco, an expert SAT tutor with a friendly and encouraging personality.
Your role is to help students prepare for the SAT exam by:
- Explaining concepts clearly and concisely
- Solving math problems step-by-step
- Teaching reading comprehension strategies
- Providing writing tips and grammar rules
- Generating practice questions

When presenting math equations, use LaTeX notation enclosed in \\( \\) for inline math or \\[ \\] for display math.
For example: \\(x^2 + y^2 = r^2\\) or \\[\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}\\]

Keep responses clear, educational, and encouraging. Break down complex problems into manageable steps.
"""
        
        # Build content list for multimodal input
        content = []
        
        # Add system prompt
        full_prompt = system_prompt
        
        # Add conversation history for context (last 5 exchanges)
        if conversation_history:
            full_prompt += "\n\nPrevious conversation:"
            for msg in conversation_history[-10:]:  # Last 10 messages (5 exchanges)
                role = "Student" if msg.get('role') == 'user' else "Prof. Coco"
                full_prompt += f"\n{role}: {msg.get('content', '')}"
        
        # Add current user message
        full_prompt += "\n\nStudent question: " + user_message
        
        if context_info:
            full_prompt += f"\n\nContext: {context_info}"
        
        content.append(full_prompt)
        
        # Add images if provided
        if image_ids:
            for image_id in image_ids:
                image_dir = os.path.join(settings.MEDIA_ROOT, 'ai_uploads', image_id)
                if os.path.exists(image_dir) and os.path.isdir(image_dir):
                    # Read image files in the directory
                    files = os.listdir(image_dir)
                    for file in files:
                        full_path = os.path.join(image_dir, file)
                        if os.path.isfile(full_path):
                            try:
                                import PIL.Image
                                with open(full_path, 'rb') as img_file:
                                    img = PIL.Image.open(img_file)
                                    content.append(img)
                            except Exception as img_error:
                                print(f"Error loading image {full_path}: {img_error}")
        
        # Generate response from Gemini
        try:
            response = model.generate_content(content)
            ai_response = response.text
        except Exception as gen_error:
            logger.error(f"Gemini generation error: {gen_error}")
            return JsonResponse({
                'success': False,
                'error': f'AI generation failed: {str(gen_error)}'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'timestamp': 'now'
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
    Generate a practice question based on user's topic/preferences using Google Gemini.
    
    POST /ai/generate-question/
    Expected: { topic: "topic name", difficulty: "easy/medium/hard" }
    """
    try:
        data = json.loads(request.body)
        topic = data.get('topic', '').strip()
        difficulty = data.get('difficulty', 'medium')
        
        if not topic:
            return JsonResponse({
                'success': False,
                'error': 'Topic is required'
            }, status=400)
        
        # Configure Gemini
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured")
            return JsonResponse({
                'success': False,
                'error': 'Gemini API key not configured. Please add GEMINI_API_KEY to .env file.'
            }, status=500)
        
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-2.5-flash with JSON response format
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                generation_config={
                    "response_mime_type": "application/json"
                }
            )
        except Exception as config_error:
            logger.error(f"Failed to configure Gemini in generate_question: {config_error}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to configure Gemini: {str(config_error)}'
            }, status=500)
        
        # Build prompt for question generation with JSON schema
        prompt = f"""Generate a {difficulty} SAT practice question about {topic}.

Return a JSON object with this exact structure:
{{
    "question": "The question text here",
    "options": {{
        "A": "Option A text",
        "B": "Option B text", 
        "C": "Option C text",
        "D": "Option D text"
    }},
    "correct_answer": "A",
    "explanation": "Detailed explanation here"
}}

Guidelines:
- Make the question realistic and follow SAT formatting standards
- Provide 4 answer choices labeled A, B, C, D
- Indicate the correct answer (A, B, C, or D)
- Provide a clear, step-by-step explanation of why the answer is correct
- Use proper spacing in text (e.g., "$10 each" not "$10each")
- For currency, use $ symbol with proper spacing
- For math expressions in JSON: 
  * Simple math: use × for multiply, ÷ for divide, ² ³ for exponents, ≤ ≥ for inequalities, √ for square root
  * Complex equations: use LaTeX with DOUBLE backslashes (\\\\) for proper JSON escaping
  * Example: "\\\\(x^2 + 2x + 1\\\\)" or "\\\\[\\\\frac{{a}}{{b}}\\\\]"
- Keep numbers and units properly formatted with spaces
- Keep it at {difficulty} difficulty level
- Make the explanation educational with step-by-step reasoning"""
        
        # Generate question
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
        except Exception as gen_error:
            logger.error(f"Gemini generation error in generate_question: {gen_error}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to generate content from Gemini: {str(gen_error)}'
            }, status=500)
        
        # Parse JSON response (should be valid JSON since we set response_mime_type)
        response_text = response_text.strip()
        
        try:
            generated_question = json.loads(response_text)
        except json.JSONDecodeError as json_error:
            logger.error(f"JSON parsing error in generate_question: {json_error}. Response: {response_text[:200]}")
            return JsonResponse({
                'success': False,
                'error': f'Failed to parse AI response as JSON: {str(json_error)}',
                'raw_response': response_text[:500]  # First 500 chars for debugging
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'question': generated_question
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
