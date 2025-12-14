#!/usr/bin/env python
"""
Quick script to setup Google OAuth in production database.
Run this with: python setup_google_oauth.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Get or create the Google Social App
google_app, created = SocialApp.objects.get_or_create(
    provider='google',
    defaults={
        'name': 'Google',
        'client_id': os.getenv('GOOGLE_CLIENT_ID', 'YOUR_GOOGLE_CLIENT_ID'),
        'secret': os.getenv('GOOGLE_CLIENT_SECRET', 'YOUR_GOOGLE_CLIENT_SECRET'),
    }
)

# Add to all sites
for site in Site.objects.all():
    google_app.sites.add(site)

if created:
    print(f"✅ Created Google Social App")
else:
    print(f"✅ Google Social App already exists")

print(f"   Client ID: {google_app.client_id[:20]}...")
print(f"   Sites: {', '.join([s.domain for s in google_app.sites.all()])}")

# Check if credentials are set
if google_app.client_id == 'YOUR_GOOGLE_CLIENT_ID':
    print("\n⚠️  WARNING: You need to set GOOGLE_CLIENT_ID in your .env file!")
if google_app.secret == 'YOUR_GOOGLE_CLIENT_SECRET':
    print("⚠️  WARNING: You need to set GOOGLE_CLIENT_SECRET in your .env file!")

print("\n✅ Google OAuth setup complete!")
