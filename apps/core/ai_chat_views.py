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
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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
        
        # Add system prompt and user message
        full_prompt = system_prompt + "\n\nStudent question: " + user_message
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
        response = model.generate_content(content)
        ai_response = response.text
        
        return JsonResponse({
            'success': True,
            'response': ai_response,
            'timestamp': 'now'
        })
        
    except Exception as e:
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
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build prompt for question generation
        prompt = f"""Generate a {difficulty} SAT practice question about {topic}.

Requirements:
1. The question should be realistic and follow SAT formatting standards
2. Provide 4 answer choices (A, B, C, D)
3. Clearly indicate the correct answer
4. Provide a detailed explanation of why the answer is correct
5. Use LaTeX notation for any math expressions: \\( \\) for inline, \\[ \\] for display

Return the response in the following JSON format:
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

Only return valid JSON, no additional text or markdown formatting."""
        
        # Generate question
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to parse JSON response
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
        
        generated_question = json.loads(response_text)
        
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
