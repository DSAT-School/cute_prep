"""
Custom adapters for django-allauth to control registration flow.
"""
from django.core.cache import cache
from django.shortcuts import render
from django.contrib import messages
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse


def is_registration_enabled():
    """
    Check if new user registration is currently enabled.
    Returns True if enabled, False otherwise.
    """
    return cache.get('user_onboarding_enabled', True)


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter to control account registration based on onboarding status.
    Only blocks NEW signups, does not affect existing user logins.
    """
    
    def is_open_for_signup(self, request):
        """
        Check if new signups are allowed.
        This is the proper method to control registration.
        """
        return is_registration_enabled()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to control OAuth registration.
    Only blocks NEW user registrations via OAuth, allows existing users to login.
    """
    
    def is_open_for_signup(self, request, sociallogin):
        """
        Check if new signups via social accounts are allowed.
        This properly blocks only NEW user creation, not existing user logins.
        """
        return is_registration_enabled()
