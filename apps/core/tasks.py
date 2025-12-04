"""
Celery tasks for async AI processing.
"""
import os
import logging
from celery import shared_task
from django.core.cache import cache
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_ai_chat_message(self, task_id, user_message, context_info='', image_ids=None, conversation_history=None, user_id=None):
    """
    Process AI chat message asynchronously using Google Gemini.
    Results are stored in cache for retrieval by task_id.
    """
    if image_ids is None:
        image_ids = []
    if conversation_history is None:
        conversation_history = []
    
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Build system prompt with SAT Buddy context
        system_prompt = """You are SAT Buddy, an expert SAT tutor with a friendly and encouraging personality.
Your role is to help students prepare for the SAT exam by:
- Explaining concepts clearly and concisely
- Solving math problems step-by-step
- Teaching reading comprehension strategies
- Providing writing tips and grammar rules
- Generating practice questions

When presenting math equations, use LaTeX notation enclosed in \\( \\) for inline math or \\[ \\] for display math.
For example: \\(x^2 + y^2 = r^2\\) or \\[\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}\\]

IMPORTANT: Keep responses SHORT and PRECISE. Be direct and clear. Avoid lengthy explanations unless specifically asked. Use bullet points when listing multiple items.
"""
        
        # Build content list for multimodal input
        content = []
        
        # Add system prompt
        full_prompt = system_prompt
        
        # Add conversation history for context (last 10 messages)
        if conversation_history:
            full_prompt += "\n\nPrevious conversation:"
            for msg in conversation_history[-10:]:
                role = "Student" if msg.get('role') == 'user' else "SAT Buddy"
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
                                logger.error(f"Error loading image {full_path}: {img_error}")
        
        # Generate response from Gemini
        response = model.generate_content(content)
        ai_response = response.text
        
        # Store result in cache (expire after 1 hour)
        cache.set(f'ai_task_{task_id}', {
            'status': 'completed',
            'response': ai_response,
            'success': True
        }, timeout=3600)
        
        logger.info(f"AI task {task_id} completed successfully")
        
    except Exception as e:
        logger.exception(f"Error in AI task {task_id}: {e}")
        
        # Store error in cache
        cache.set(f'ai_task_{task_id}', {
            'status': 'failed',
            'error': str(e),
            'success': False
        }, timeout=3600)
        
        # Retry on certain errors
        if 'quota' in str(e).lower() or 'rate limit' in str(e).lower():
            raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds


@shared_task(bind=True, max_retries=3)
def process_ai_question_generation(self, task_id, topic, difficulty='medium'):
    """
    Generate SAT practice question asynchronously.
    Results are stored in cache for retrieval by task_id.
    """
    try:
        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Build prompt for question generation
        prompt = f"""You are SAT Buddy, an expert SAT tutor. Generate a {difficulty} SAT practice question about {topic}.

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

CRITICAL Guidelines:
- The question MUST be SELF-CONTAINED and COMPLETE - include all necessary information
- DO NOT reference external passages, texts, or materials that aren't provided
- If the question requires a passage (reading comprehension), INCLUDE THE FULL PASSAGE in the question text
- For math questions, provide all given values and constraints in the question itself
- Make the question realistic and follow SAT formatting standards
- Provide 4 answer choices labeled A, B, C, D
- Indicate the correct answer (A, B, C, or D)
- Provide a clear, concise explanation of why the answer is correct
- Use proper spacing in text (e.g., "$10 each" not "$10each")
- For currency, use $ symbol with proper spacing
- For math expressions in JSON: 
  * Simple math: use × for multiply, ÷ for divide, ² ³ for exponents, ≤ ≥ for inequalities, √ for square root
  * Complex equations: use LaTeX with DOUBLE backslashes (\\\\) for proper JSON escaping
  * Example: "\\\\(x^2 + 2x + 1\\\\)" or "\\\\[\\\\frac{{a}}{{b}}\\\\]"
- Keep numbers and units properly formatted with spaces
- Keep it at {difficulty} difficulty level"""
        
        # Generate question
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Parse JSON response
        import json
        generated_question = json.loads(response_text)
        
        # Store result in cache
        cache.set(f'ai_task_{task_id}', {
            'status': 'completed',
            'question': generated_question,
            'success': True
        }, timeout=3600)
        
        logger.info(f"Question generation task {task_id} completed successfully")
        
    except Exception as e:
        logger.exception(f"Error in question generation task {task_id}: {e}")
        
        cache.set(f'ai_task_{task_id}', {
            'status': 'failed',
            'error': str(e),
            'success': False
        }, timeout=3600)
        
        if 'quota' in str(e).lower() or 'rate limit' in str(e).lower():
            raise self.retry(exc=e, countdown=60)
