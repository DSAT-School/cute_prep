"""
AI Question Extractor View
Extracts question details from images using Gemini AI.
"""

import os
import json
import base64
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from apps.core.decorators import instructor_required
import google.generativeai as genai


@instructor_required
@require_http_methods(["POST"])
def extract_question_from_image(request):
    """
    Extract math question details from an uploaded image using Gemini AI.
    
    Returns JSON with:
    - stimulus: Optional passage/context
    - stem: The main question text
    - question_type: MCQ or SPR
    - mcq_options: Dict with A, B, C, D options (if MCQ)
    - mcq_answer: Correct answer letter (if MCQ)
    """
    try:
        # Get uploaded image
        if 'image' not in request.FILES:
            return JsonResponse({'error': 'No image provided'}, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file size (10MB max)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({'error': 'File size must be less than 10MB'}, status=400)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png']
        if image_file.content_type not in allowed_types:
            return JsonResponse({'error': 'Invalid file type. Only JPEG and PNG are allowed'}, status=400)
        
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return JsonResponse({'error': 'AI service not configured'}, status=500)
        
        genai.configure(api_key=api_key)
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Create the prompt for Gemini
        prompt = """
You are an expert at extracting SAT Math questions from images. Analyze this image and extract the following information in JSON format:

1. **stimulus**: Any passage, context, or setup information that appears before the main question (if present). This could include:
   - Data tables or graphs descriptions
   - Word problem setup
   - Mathematical context
   If there's no stimulus, return an empty string.

2. **stem**: The main question text. This is the actual question being asked.

3. **question_type**: Determine if this is:
   - "MCQ" for multiple choice questions (with options A, B, C, D)
   - "SPR" for student-produced response (grid-in) questions where students enter their own answer

4. **mcq_options**: If it's an MCQ, extract all options as a dictionary with keys A, B, C, D. If it's SPR, return null.

5. **mcq_answer**: For MCQ questions:
   - If the correct answer is marked/highlighted in the image, extract it
   - If not marked, SOLVE THE PROBLEM and determine the correct answer yourself
   - Return the letter (A, B, C, or D) of the correct answer
   - If MCQ but you cannot solve it, return null

6. **spr_answer**: For SPR (grid-in) questions:
   - SOLVE THE PROBLEM and determine the correct numerical answer
   - Provide all acceptable forms as a JSON array (e.g., ["2.5", "5/2", "2.5"])
   - Include decimal and fraction forms when applicable
   - If it's MCQ or you cannot solve it, return null

7. **explanation**: A detailed step-by-step explanation of how to solve the problem:
   - Show all mathematical steps
   - Explain the reasoning and approach
   - Use LaTeX for all math notation
   - This should be comprehensive enough for a student to understand the solution

IMPORTANT FORMATTING RULES:
- Preserve ALL mathematical notation using LaTeX format
- Use $ for inline math (e.g., $x^2 + 3x + 5$)
- Use $$ for display math (e.g., $$\\frac{a}{b}$$)
- Common LaTeX examples:
  - Fractions: $\\frac{numerator}{denominator}$
  - Exponents: $x^2$, $x^{10}$
  - Subscripts: $x_1$, $x_{10}$
  - Square roots: $\\sqrt{x}$, $\\sqrt[3]{x}$
  - Greek letters: $\\pi$, $\\theta$, $\\alpha$
  - Inequalities: $\\leq$, $\\geq$, $\\neq$
  - Functions: $\\sin(x)$, $\\cos(x)$, $\\log(x)$
- Keep HTML formatting for structure (line breaks, emphasis, etc.)

Return ONLY a valid JSON object with this exact structure:
{
    "stimulus": "string or empty",
    "stem": "string",
    "question_type": "MCQ or SPR",
    "mcq_options": {
        "A": "option text",
        "B": "option text",
        "C": "option text",
        "D": "option text"
    } or null,
    "mcq_answer": "A, B, C, or D" or null,
    "spr_answer": ["answer1", "answer2"] or null,
    "explanation": "detailed solution explanation with LaTeX math notation"
}

Do not include any text before or after the JSON object.
"""
        
        # Use Gemini Vision model
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Generate response
        response = model.generate_content([
            prompt,
            {
                'mime_type': image_file.content_type,
                'data': base64.b64encode(image_bytes).decode('utf-8')
            }
        ])
        
        # Parse the response
        response_text = response.text.strip()
        
        # Remove markdown code block if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        extracted_data = json.loads(response_text)
        
        # Validate required fields
        if 'stem' not in extracted_data or not extracted_data['stem']:
            return JsonResponse({'error': 'Could not extract question stem from image'}, status=400)
        
        if 'question_type' not in extracted_data:
            extracted_data['question_type'] = 'MCQ'  # Default to MCQ
        
        # Ensure question_type is valid
        if extracted_data['question_type'] not in ['MCQ', 'SPR']:
            extracted_data['question_type'] = 'MCQ'
        
        return JsonResponse(extracted_data)
        
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': f'Failed to parse AI response: {str(e)}',
            'raw_response': response_text if 'response_text' in locals() else 'No response'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)
