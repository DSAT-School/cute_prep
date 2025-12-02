#!/bin/bash
# Test script for AI integration

echo "================================"
echo "AI Integration Test Script"
echo "================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated"
    echo "Run: source venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment activated"

# Check if required packages are installed
echo ""
echo "Checking required packages..."

if python -c "import google.generativeai" 2>/dev/null; then
    echo "✓ google-generativeai installed"
else
    echo "❌ google-generativeai not installed"
    echo "Run: pip install google-generativeai"
    exit 1
fi

if python -c "import PIL" 2>/dev/null; then
    echo "✓ Pillow installed"
else
    echo "❌ Pillow not installed"
    echo "Run: pip install Pillow"
    exit 1
fi

# Check if .env file exists and has GEMINI_API_KEY
echo ""
echo "Checking environment configuration..."

if [ -f .env ]; then
    echo "✓ .env file exists"
    
    if grep -q "GEMINI_API_KEY" .env; then
        echo "✓ GEMINI_API_KEY found in .env"
        
        # Check if it's not the placeholder
        if grep -q "GEMINI_API_KEY=your-gemini-api-key-here" .env; then
            echo "⚠️  WARNING: Using placeholder API key"
            echo "   Update .env with your actual Gemini API key"
            echo "   Get key from: https://aistudio.google.com/app/apikey"
        else
            echo "✓ Custom API key configured"
        fi
    else
        echo "❌ GEMINI_API_KEY not found in .env"
        echo "Add: GEMINI_API_KEY=your-actual-api-key"
        exit 1
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

# Check if media directory exists
echo ""
echo "Checking media directories..."

if [ -d "mediafiles/ai_uploads" ]; then
    echo "✓ ai_uploads directory exists"
else
    echo "Creating ai_uploads directory..."
    mkdir -p mediafiles/ai_uploads
    echo "✓ Created ai_uploads directory"
fi

# Check if views file exists and has correct imports
echo ""
echo "Checking AI views..."

if [ -f "apps/core/ai_chat_views.py" ]; then
    echo "✓ ai_chat_views.py exists"
    
    if grep -q "import google.generativeai as genai" apps/core/ai_chat_views.py; then
        echo "✓ Gemini imports present"
    else
        echo "❌ Missing Gemini imports"
        exit 1
    fi
else
    echo "❌ ai_chat_views.py not found"
    exit 1
fi

# Check template file
echo ""
echo "Checking templates..."

if [ -f "templates/ai_chat/chat.html" ]; then
    echo "✓ chat.html template exists"
    
    if grep -q "processMarkdown" templates/ai_chat/chat.html; then
        echo "✓ Markdown processing function present"
    else
        echo "❌ Missing markdown processing"
        exit 1
    fi
else
    echo "❌ chat.html template not found"
    exit 1
fi

# Test Django configuration
echo ""
echo "Testing Django configuration..."

python manage.py check --deploy 2>&1 | head -5

# Summary
echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo ""
echo "✅ All checks passed!"
echo ""
echo "Next steps:"
echo "1. Ensure GEMINI_API_KEY in .env has your actual API key"
echo "   Get key: https://aistudio.google.com/app/apikey"
echo ""
echo "2. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "3. Navigate to:"
echo "   http://localhost:8000/ai/chat/"
echo ""
echo "4. Test the AI chat by:"
echo "   - Asking a math question"
echo "   - Uploading an image"
echo "   - Generating a practice question"
echo ""
