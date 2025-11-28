# Timezone Feature Documentation

## Overview
This Django application now supports global timezone handling, allowing users from anywhere in the world to see times in their local timezone while storing all datetimes in UTC in the database.

## Architecture

### Components

#### 1. **TimezoneMiddleware** (`apps/core/middleware.py`)
- Automatically detects and activates the appropriate timezone for each request
- Priority order:
  1. User's saved timezone preference (from User model)
  2. Session timezone (detected by JavaScript)
  3. HTTP header `X-Timezone`
  4. Defaults to UTC

#### 2. **User Model Timezone Field** (`apps/core/models.py`)
- Added `timezone` field to store user preferences
- CharField with max 63 characters
- Default: `'UTC'`
- Stores IANA timezone names (e.g., `'America/New_York'`, `'Asia/Tokyo'`)

#### 3. **Client-Side Detection** (`templates/base.html`)
- JavaScript automatically detects browser timezone using `Intl.DateTimeFormat().resolvedOptions().timeZone`
- Sends detected timezone to server via AJAX
- Stored in session for immediate use
- Optionally updates authenticated user's profile

#### 4. **Timezone Utilities** (`apps/core/utils/timezone.py`)
- `validate_timezone(tzname)` - Validate timezone names
- `convert_to_user_timezone(dt, user_timezone)` - Convert UTC datetime to user timezone
- `format_datetime_in_timezone(dt, user_timezone, format_str)` - Format datetime in user timezone
- `get_timezone_offset(tzname)` - Get UTC offset for a timezone
- `get_user_timezone_from_request(request)` - Extract timezone from request

#### 5. **Context Processor** (`apps/core/context_processors.py`)
- Adds timezone information to all template contexts
- Available variables:
  - `TIMEZONE_ENABLED` - Boolean flag if timezone feature is enabled
  - `current_timezone` - Currently activated timezone name
  - `user_timezone` - Authenticated user's saved timezone

#### 6. **API Endpoint** (`apps/core/views.py`)
- `POST /api/set-timezone/` - Set timezone in session
- Accepts JSON: `{"timezone": "America/New_York"}`
- Validates timezone before storing
- Updates authenticated user's profile if timezone is still default UTC

## Settings Configuration

In `config/settings/base.py`:

```python
# Timezone settings
USE_TZ = True  # Enable timezone support
TIME_ZONE = 'UTC'  # Server/database timezone (always UTC)
USER_TIME_ZONE_ENABLED = True  # Enable per-user timezone detection

# Middleware (includes TimezoneMiddleware)
MIDDLEWARE = [
    # ... other middleware
    "apps.core.middleware.TimezoneMiddleware",
    # ... other middleware
]

# Template context processors (includes user_timezone)
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... other processors
                "apps.core.context_processors.user_timezone",
            ],
        },
    },
]
```

## Usage

### In Django Templates

```django
{# Display datetime in user's timezone #}
{{ event.start_time }}  {# Automatically in user's timezone #}

{# Check if timezone is enabled #}
{% if TIMEZONE_ENABLED %}
    <p>Your timezone: {{ current_timezone }}</p>
{% endif %}

{# Format with timezone #}
{{ event.start_time|date:"Y-m-d H:i:s T" }}  {# Includes timezone abbreviation #}
```

### In Python Code

```python
from django.utils import timezone
from apps.core.utils.timezone import convert_to_user_timezone

# Get current time in UTC (always store in UTC)
now_utc = timezone.now()

# Convert to user's timezone for display
user_tz = request.user.timezone
now_user = convert_to_user_timezone(now_utc, user_tz)

# Get currently activated timezone
current_tz = timezone.get_current_timezone_name()
```

### In API Responses

The `UserSerializer` now includes the `timezone` field:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "john_doe",
  "email": "john@example.com",
  "timezone": "America/New_York",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Setting Timezone via API

```javascript
// Client-side: Set timezone
fetch('/api/set-timezone/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrfToken
  },
  body: JSON.stringify({
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
  })
});
```

```python
# Server-side: Update user timezone
user.timezone = 'Europe/London'
user.save(update_fields=['timezone'])
```

## Best Practices

### 1. **Always Store UTC in Database**
- Store all datetime fields in UTC
- Use Django's `timezone.now()` for current time
- Never store local time in the database

```python
# ✅ Good
event.start_time = timezone.now()

# ❌ Bad
event.start_time = datetime.now()  # Naive datetime, no timezone
```

### 2. **Convert for Display Only**
- Convert to user timezone only when displaying
- Keep calculations and comparisons in UTC

```python
# ✅ Good: Convert for display
display_time = convert_to_user_timezone(event.start_time, user.timezone)

# ✅ Good: Compare in UTC
if timezone.now() > event.start_time:
    # Event has passed
```

### 3. **Use Timezone-Aware Datetimes**
- Always use timezone-aware datetimes
- Check with `timezone.is_aware(dt)`

```python
from django.utils import timezone

# ✅ Good
aware_dt = timezone.now()
assert timezone.is_aware(aware_dt)

# ❌ Bad
naive_dt = datetime.now()
assert not timezone.is_aware(naive_dt)
```

### 4. **Handle User Input Carefully**
- User input may be in their local timezone
- Convert to UTC before saving

```python
# User submits time in their timezone
user_input = "2024-01-01 14:00:00"
user_tz = zoneinfo.ZoneInfo(request.user.timezone)

# Parse as user's local time
local_dt = datetime.strptime(user_input, "%Y-%m-%d %H:%M:%S")
local_dt = local_dt.replace(tzinfo=user_tz)

# Convert to UTC for storage
utc_dt = local_dt.astimezone(timezone.utc)
event.start_time = utc_dt
```

## Testing

Run timezone-specific tests:

```bash
pytest tests/test_timezone.py
```

The test suite covers:
- Middleware timezone activation
- Timezone utility functions
- User model timezone field
- API endpoint validation
- Client-side detection
- Template context processors

## Common Timezone Names

The system supports all IANA timezones. Common ones include:

**Americas:**
- `America/New_York` (EST/EDT)
- `America/Chicago` (CST/CDT)
- `America/Denver` (MST/MDT)
- `America/Los_Angeles` (PST/PDT)
- `America/Toronto`, `America/Vancouver`
- `America/Mexico_City`, `America/Sao_Paulo`

**Europe:**
- `Europe/London` (GMT/BST)
- `Europe/Paris`, `Europe/Berlin` (CET/CEST)
- `Europe/Rome`, `Europe/Madrid`
- `Europe/Moscow` (MSK)

**Asia:**
- `Asia/Dubai` (GST)
- `Asia/Kolkata` (IST)
- `Asia/Bangkok`, `Asia/Singapore` (ICT/SGT)
- `Asia/Hong_Kong`, `Asia/Tokyo` (HKT/JST)
- `Asia/Seoul` (KST)

**Pacific:**
- `Australia/Sydney`, `Australia/Melbourne` (AEDT/AEST)
- `Pacific/Auckland` (NZDT/NZST)

## Troubleshooting

### Issue: Times not converting
**Solution:** Ensure `USE_TZ = True` and middleware is installed

### Issue: Invalid timezone errors
**Solution:** Use IANA timezone names (e.g., `'America/New_York'`, not `'EST'`)

### Issue: JavaScript detection not working
**Solution:** Check browser console for errors, verify CSRF token

### Issue: User timezone not persisting
**Solution:** Verify User model has timezone field and migrations are applied

## Migration

To add timezone support to an existing project:

1. Add timezone field to User model
2. Create and run migration: `python manage.py migrate`
3. Add middleware to settings
4. Add context processor to settings
5. Update templates with timezone detection JavaScript
6. Test thoroughly with users in different timezones

## Security Considerations

- **Validation:** All timezone inputs are validated before use
- **CSRF Protection:** Timezone endpoint requires CSRF token
- **User Privacy:** Timezone is optional and can be changed
- **Default Fallback:** Invalid timezones fall back to UTC

## Performance

- **Caching:** Timezone objects are cached by Python's `zoneinfo`
- **Middleware Overhead:** Minimal (~1-2ms per request)
- **Database Impact:** Single varchar field per user
- **Client-Side:** Single AJAX call per session

## Future Enhancements

Potential improvements:
- IP-based timezone detection fallback
- Admin interface for managing user timezones
- Timezone picker widget in user settings
- Display timezone abbreviations in templates
- Support for "auto-detect" vs "manual" preference
- Analytics on timezone distribution
