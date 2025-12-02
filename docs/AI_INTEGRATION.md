# AI Integration - Ask Prof. Coco

## Overview
The Ask Prof. Coco feature is now fully integrated with Google Gemini AI (gemini-2.5-flash model). This provides students with an intelligent AI tutor that can:

- Answer SAT-related questions
- Explain concepts with step-by-step solutions
- Analyze uploaded images (handwritten problems, diagrams, etc.)
- Generate custom practice questions
- Render mathematical expressions using LaTeX

## Setup Instructions

### 1. Get Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 2. Configure Environment

Add your API key to the `.env` file:

```bash
GEMINI_API_KEY=your-actual-gemini-api-key-here
```

Replace `your-actual-gemini-api-key-here` with your actual API key from Google AI Studio.

### 3. Restart the Server

After adding the API key, restart your Django development server:

```bash
source venv/bin/activate
python manage.py runserver
```

## Features

### Chat with AI
- Navigate to `/ai/chat/` or click "Ask Prof. Coco" in the sidebar
- Type your question and press Enter or click Send
- The AI will respond with formatted text, including math expressions

### Image Upload
- Click the paperclip icon to upload images
- Supports JPG, PNG, and GIF (max 5MB)
- AI can analyze handwritten problems, diagrams, graphs, etc.
- Send images along with your question for context

### Generate Practice Questions
- Use the "Generate a practice question" quick action
- Specify topic and difficulty level
- AI generates SAT-style questions with explanations

### LaTeX Math Rendering
The system automatically renders mathematical expressions:
- Inline math: `\( x^2 + y^2 = r^2 \)`
- Display math: `\[ \frac{-b \pm \sqrt{b^2-4ac}}{2a} \]`

## Technical Details

### Backend Implementation

**File:** `apps/core/ai_chat_views.py`

Key functions:
- `ai_chat_message()` - Handles chat messages with Gemini AI
- `ai_upload_image()` - Processes image uploads
- `ai_generate_question()` - Generates SAT practice questions

### Frontend Implementation

**File:** `templates/ai_chat/chat.html`

Key features:
- Markdown processing for formatted responses
- MathJax integration for LaTeX rendering
- Image preview and upload handling
- Typing indicators for better UX

### Configuration

**File:** `config/settings/base.py`

```python
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
```

### Dependencies

**File:** `requirements/base.txt`

```
google-generativeai  # Google Gemini AI SDK
Pillow  # Image processing for multimodal inputs
```

## API Endpoints

### POST /ai/chat/message/
Send a message to the AI tutor.

**Request:**
```json
{
    "message": "Explain quadratic equations",
    "context": "optional context",
    "images": ["image_id1", "image_id2"]
}
```

**Response:**
```json
{
    "success": true,
    "response": "Quadratic equations are...",
    "timestamp": "now"
}
```

### POST /ai/upload-image/
Upload an image for AI analysis.

**Request:** Multipart form data with `image` file

**Response:**
```json
{
    "success": true,
    "file_url": "/media/ai_uploads/...",
    "file_path": "ai_uploads/...",
    "message": "Image uploaded successfully"
}
```

### POST /ai/generate-question/
Generate a practice question.

**Request:**
```json
{
    "topic": "Linear Equations",
    "difficulty": "medium"
}
```

**Response:**
```json
{
    "success": true,
    "question": {
        "question": "If 3x + 5 = 20, what is x?",
        "options": {
            "A": "5",
            "B": "10",
            "C": "15",
            "D": "20"
        },
        "correct_answer": "A",
        "explanation": "Subtract 5 from both sides..."
    }
}
```

## System Prompt

The AI tutor uses a carefully crafted system prompt to ensure:
- Educational and encouraging tone
- Step-by-step explanations
- Proper LaTeX formatting for math
- SAT-focused content

**Prompt excerpt:**
```
You are Prof. Coco, an expert SAT tutor with a friendly and encouraging personality.
When presenting math equations, use LaTeX notation enclosed in \( \) for inline math 
or \[ \] for display math.
```

## Error Handling

The system includes comprehensive error handling:
- Invalid API key detection
- Rate limiting awareness
- Image format/size validation
- JSON parsing error recovery
- Network timeout handling

## Performance Considerations

- Model: `gemini-2.5-flash` (fast inference)
- Image size limit: 5MB per upload
- Supports multiple images per message
- Async processing for better UX

## Testing

### Manual Testing

1. **Basic Chat:**
   - Send: "What is the Pythagorean theorem?"
   - Verify: Response includes LaTeX formula `\( a^2 + b^2 = c^2 \)`

2. **Image Upload:**
   - Upload an image of a math problem
   - Ask: "Can you solve this problem?"
   - Verify: AI analyzes the image and provides solution

3. **Question Generation:**
   - Click "Generate a practice question"
   - Enter topic: "Algebra"
   - Verify: Receives SAT-style question with options

### Verify LaTeX Rendering

Open browser console and check:
```javascript
MathJax.typesetPromise()
```

Should return without errors if MathJax is working.

## Troubleshooting

### API Key Not Working
- Verify the key is correct in `.env`
- Check Google AI Studio for API usage/limits
- Ensure no extra spaces in the key

### LaTeX Not Rendering
- Check browser console for MathJax errors
- Verify `base_dashboard.html` loads MathJax CDN
- Clear browser cache

### Images Not Processing
- Check file size (must be < 5MB)
- Verify file format (JPG, PNG, GIF only)
- Check `mediafiles/ai_uploads/` directory exists
- Verify Pillow is installed: `pip show Pillow`

### AI Responses Slow
- Normal for first request (model loading)
- Check network connection
- Consider caching frequently asked questions
- Monitor Google AI Studio quota

## Future Enhancements

- [ ] Chat history persistence in database
- [ ] Conversation context management
- [ ] Response streaming for real-time updates
- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Personalized study recommendations
- [ ] Progress tracking integration

## Security Notes

⚠️ **Important:**
- Never commit `.env` file with actual API keys
- Keep `GEMINI_API_KEY` secret
- Implement rate limiting in production
- Monitor API usage to avoid unexpected costs
- Validate all user inputs before sending to AI
- Sanitize AI responses before rendering

## Resources

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [MathJax Documentation](https://docs.mathjax.org/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
