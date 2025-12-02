#!/usr/bin/env python
"""
Quick test script to verify Gemini API integration.
"""
import os
import sys
import django

# Add project root to path
sys.path.insert(0, '/home/raju/dsatschool-product/practice_portal')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.conf import settings
import google.generativeai as genai

def test_gemini_connection():
    """Test basic Gemini API connection."""
    print("=" * 60)
    print("Testing Gemini API Connection")
    print("=" * 60)
    print()
    
    # Check API key
    print(f"✓ API Key configured: {bool(settings.GEMINI_API_KEY)}")
    print(f"✓ API Key length: {len(settings.GEMINI_API_KEY)}")
    print()
    
    try:
        # Configure Gemini
        print("Configuring Gemini...")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        print("✓ Gemini configured successfully")
        print()
        
        # List available models
        print("Available models:")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(f"  - {model.name}")
        print()
        
        # Test with gemini-1.5-flash
        print("Testing gemini-1.5-flash model...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✓ Model initialized")
        print()
        
        # Test simple generation
        print("Testing content generation...")
        test_prompt = "Say 'Hello, I am Prof. Coco!' in exactly those words."
        response = model.generate_content(test_prompt)
        print(f"✓ Response received: {response.text[:100]}")
        print()
        
        # Test with math LaTeX
        print("Testing math LaTeX generation...")
        math_prompt = "Write the quadratic formula using LaTeX notation with \\( \\) for inline math."
        response = model.generate_content(math_prompt)
        print(f"✓ Math response: {response.text[:200]}")
        print()
        
        print("=" * 60)
        print("✅ All tests passed! Gemini integration is working.")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ ERROR occurred:")
        print("=" * 60)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_gemini_connection()
    sys.exit(0 if success else 1)
