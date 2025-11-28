"""Tests for timezone functionality."""
import pytest
from django.utils import timezone
from django.test import RequestFactory
from apps.core.models import User
from apps.core.middleware import TimezoneMiddleware
from apps.core.utils.timezone import (
    validate_timezone,
    convert_to_user_timezone,
    get_timezone_offset,
    get_user_timezone_from_request,
)
from datetime import datetime
import zoneinfo


@pytest.mark.django_db
class TestTimezoneMiddleware:
    """Test TimezoneMiddleware functionality."""
    
    def test_middleware_activates_user_timezone(self, user_factory):
        """Test that middleware activates user's saved timezone."""
        user = user_factory(timezone='America/New_York')
        request = RequestFactory().get('/')
        request.user = user
        request.session = {}
        
        middleware = TimezoneMiddleware(lambda r: None)
        middleware(request)
        
        # Timezone should be activated
        current_tz = timezone.get_current_timezone_name()
        assert current_tz == 'America/New_York'
    
    def test_middleware_uses_session_timezone(self):
        """Test that middleware uses session timezone if no user timezone."""
        request = RequestFactory().get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.session = {'detected_timezone': 'Europe/London'}
        
        middleware = TimezoneMiddleware(lambda r: None)
        middleware(request)
        
        current_tz = timezone.get_current_timezone_name()
        assert current_tz == 'Europe/London'
    
    def test_middleware_handles_invalid_timezone(self):
        """Test that middleware handles invalid timezone gracefully."""
        request = RequestFactory().get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.session = {'detected_timezone': 'Invalid/Timezone'}
        
        middleware = TimezoneMiddleware(lambda r: None)
        # Should not raise exception
        middleware(request)


@pytest.mark.django_db
class TestTimezoneUtils:
    """Test timezone utility functions."""
    
    def test_validate_timezone_valid(self):
        """Test validation of valid timezones."""
        assert validate_timezone('UTC') is True
        assert validate_timezone('America/New_York') is True
        assert validate_timezone('Asia/Tokyo') is True
        assert validate_timezone('Europe/London') is True
    
    def test_validate_timezone_invalid(self):
        """Test validation of invalid timezones."""
        assert validate_timezone('Invalid/Zone') is False
        assert validate_timezone('NotATimezone') is False
        assert validate_timezone('') is False
    
    def test_convert_to_user_timezone(self):
        """Test datetime conversion to user timezone."""
        # Create a UTC datetime
        utc_dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=zoneinfo.ZoneInfo('UTC'))
        
        # Convert to New York time (UTC-5 in winter)
        ny_dt = convert_to_user_timezone(utc_dt, 'America/New_York')
        assert ny_dt.hour == 7  # 12:00 UTC = 07:00 EST
        
        # Convert to Tokyo time (UTC+9)
        tokyo_dt = convert_to_user_timezone(utc_dt, 'Asia/Tokyo')
        assert tokyo_dt.hour == 21  # 12:00 UTC = 21:00 JST
    
    def test_convert_naive_datetime(self):
        """Test conversion of naive datetime (assumes UTC)."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        converted = convert_to_user_timezone(naive_dt, 'America/New_York')
        
        # Should work without raising exception
        assert converted is not None
        assert timezone.is_aware(converted)
    
    def test_get_timezone_offset(self):
        """Test getting timezone offset."""
        utc_offset = get_timezone_offset('UTC')
        assert utc_offset == '+00:00'
        
        # New York offset (varies by DST, but should be valid format)
        ny_offset = get_timezone_offset('America/New_York')
        assert ny_offset is not None
        assert ny_offset[0] in ['+', '-']
        assert ':' in ny_offset
    
    def test_get_timezone_offset_invalid(self):
        """Test getting offset for invalid timezone."""
        offset = get_timezone_offset('Invalid/Zone')
        assert offset is None
    
    def test_get_user_timezone_from_request_authenticated(self, user_factory):
        """Test extracting timezone from authenticated user."""
        user = user_factory(timezone='Europe/Paris')
        request = RequestFactory().get('/')
        request.user = user
        request.session = {}
        request.META = {}
        
        tz = get_user_timezone_from_request(request)
        assert tz == 'Europe/Paris'
    
    def test_get_user_timezone_from_session(self):
        """Test extracting timezone from session."""
        request = RequestFactory().get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.session = {'detected_timezone': 'Asia/Singapore'}
        request.META = {}
        
        tz = get_user_timezone_from_request(request)
        assert tz == 'Asia/Singapore'
    
    def test_get_user_timezone_from_header(self):
        """Test extracting timezone from HTTP header."""
        request = RequestFactory().get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.session = {}
        request.META = {'HTTP_X_TIMEZONE': 'Australia/Sydney'}
        
        tz = get_user_timezone_from_request(request)
        assert tz == 'Australia/Sydney'
    
    def test_get_user_timezone_default(self):
        """Test default timezone when no source available."""
        request = RequestFactory().get('/')
        request.user = type('User', (), {'is_authenticated': False})()
        request.session = {}
        request.META = {}
        
        tz = get_user_timezone_from_request(request)
        assert tz == 'UTC'


@pytest.mark.django_db
class TestUserTimezoneField:
    """Test User model timezone field."""
    
    def test_user_default_timezone(self, user_factory):
        """Test that new users get UTC as default timezone."""
        user = user_factory()
        assert user.timezone == 'UTC'
    
    def test_user_custom_timezone(self, user_factory):
        """Test setting custom timezone for user."""
        user = user_factory(timezone='America/Los_Angeles')
        assert user.timezone == 'America/Los_Angeles'
        
        # Refresh from database
        user.refresh_from_db()
        assert user.timezone == 'America/Los_Angeles'
    
    def test_user_timezone_in_serializer(self, user_factory, api_client):
        """Test that timezone is included in API responses."""
        user = user_factory(timezone='Europe/Berlin')
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/users/me/')
        assert response.status_code == 200
        assert response.data['timezone'] == 'Europe/Berlin'


@pytest.mark.django_db
class TestSetTimezoneView:
    """Test set_timezone view."""
    
    def test_set_timezone_valid(self, api_client):
        """Test setting valid timezone in session."""
        response = api_client.post(
            '/api/set-timezone/',
            {'timezone': 'Asia/Kolkata'},
            format='json'
        )
        
        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        assert response.json()['timezone'] == 'Asia/Kolkata'
    
    def test_set_timezone_invalid(self, api_client):
        """Test setting invalid timezone."""
        response = api_client.post(
            '/api/set-timezone/',
            {'timezone': 'Invalid/Timezone'},
            format='json'
        )
        
        assert response.status_code == 400
        assert response.json()['status'] == 'error'
    
    def test_set_timezone_updates_authenticated_user(self, user_factory, api_client):
        """Test that timezone updates authenticated user's profile."""
        user = user_factory(timezone='UTC')
        api_client.force_authenticate(user=user)
        
        response = api_client.post(
            '/api/set-timezone/',
            {'timezone': 'America/Chicago'},
            format='json'
        )
        
        assert response.status_code == 200
        
        # Verify user's timezone was updated
        user.refresh_from_db()
        assert user.timezone == 'America/Chicago'
