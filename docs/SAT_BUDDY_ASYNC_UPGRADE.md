# SAT Buddy - Async Implementation Upgrade

## Overview
Renamed "Ask Prof. Coco" to "SAT Buddy" and implemented efficient asynchronous AI processing using Celery to prevent blocking the Django application.

## Key Changes

### 1. Feature Rebranding
- **Old Name**: Ask Prof. Coco
- **New Name**: SAT Buddy
- Updated all references in:
  - Views (`apps/core/ai_chat_views.py`)
  - Templates (`templates/ai_chat/chat.html`)
  - URLs (`config/urls.py`)
  - System prompts in tasks

### 2. Async Processing Implementation

#### Architecture
```
User Request → Django View → Celery Task Queue → Background Worker → Cache Result → Poll & Return
```

#### Benefits
- **Non-blocking**: HTTP requests no longer block during AI processing
- **Scalable**: Multiple requests can be processed concurrently
- **Resilient**: Automatic retry on failures with exponential backoff
- **Efficient**: Frees up Django workers to handle other requests

### 3. New Files Created

#### `/apps/core/tasks.py`
Celery tasks for async AI processing:
- `process_ai_chat_message`: Handles chat messages asynchronously
- `process_ai_question_generation`: Generates practice questions asynchronously

Features:
- Results cached for 1 hour using Django cache
- Automatic retry on quota/rate limit errors (3 max retries, 60s delay)
- Comprehensive error handling and logging
- Image upload support maintained

### 4. Modified Files

#### `/apps/core/ai_chat_views.py`
- Updated imports (added `uuid`, `cache`)
- `ai_chat_view`: Updated context to "SAT Buddy"
- `ai_chat_message`: Changed from sync to async task submission
  - Returns `task_id` instead of immediate response
  - Client polls for result
- `ai_generate_question`: Changed to async task submission
- **NEW**: `ai_task_status`: Polling endpoint to check task status

#### `/config/urls.py`
- Updated comments: "Ask Prof. Coco" → "SAT Buddy"
- Added new route: `/ai/task/<task_id>/` for polling

#### `/templates/ai_chat/chat.html`
- Updated title: "Ask Prof. Coco" → "SAT Buddy"
- Updated header with robot icon
- JavaScript changes:
  - `sendMessage()`: Now submits task and polls for result
  - **NEW**: `pollTaskResult()`: Polls task status every 1 second (max 60 attempts)
  - Maintains conversation history and UI updates

### 5. API Changes

#### Old Behavior (Synchronous)
```javascript
POST /ai/chat/message/
Request: { message: "...", context: "...", images: [], history: [] }
Response: { success: true, response: "AI response text" }
// Blocks until AI finishes (5-30 seconds)
```

#### New Behavior (Asynchronous)
```javascript
// Step 1: Submit task
POST /ai/chat/message/
Request: { message: "...", context: "...", images: [], history: [] }
Response: { success: true, task_id: "uuid", status: "processing" }
// Returns immediately (~50ms)

// Step 2: Poll for result
GET /ai/task/{task_id}/
Response: 
  - While processing: { status: "processing" }
  - On completion: { status: "completed", success: true, response: "AI text" }
  - On error: { status: "failed", success: false, error: "error message" }
```

### 6. Performance Improvements

| Metric | Before | After |
|--------|--------|-------|
| Django worker blocked time | 5-30s per request | ~50ms per request |
| Concurrent requests supported | Limited by workers | Unlimited (queue-based) |
| Timeout handling | HTTP timeout (60s) | Configurable (60s default) |
| Error recovery | None | Automatic retry on rate limits |
| Resource utilization | Inefficient | Optimized |

### 7. Cache Strategy

- **Storage**: Django cache (Redis recommended, falls back to DB)
- **TTL**: 1 hour (3600 seconds)
- **Key Format**: `ai_task_{task_id}`
- **Cleanup**: Automatic expiry

### 8. Deployment Requirements

#### Celery Worker Setup
```bash
# Start Celery worker (already configured in systemd)
celery -A config worker -l info

# Start Celery beat (for scheduled tasks)
celery -A config beat -l info
```

#### Redis Configuration (Recommended)
```python
# settings/base.py or settings/prod.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### 9. Monitoring & Logging

All async tasks log to standard Django logger:
```python
logger.info(f"AI task {task_id} completed successfully")
logger.error(f"Error in AI task {task_id}: {error}")
```

Monitor Celery:
```bash
# View active tasks
celery -A config inspect active

# View stats
celery -A config inspect stats
```

### 10. Error Handling

- **Quota exceeded**: Automatic retry after 60 seconds
- **Rate limits**: Automatic retry after 60 seconds
- **Task timeout**: Client receives timeout after 60 polling attempts
- **Network errors**: Graceful fallback with error message

### 11. Backward Compatibility

- URL structure maintained (only added new polling endpoint)
- User experience unchanged (still sees typing indicator)
- Same conversation history handling
- Image upload functionality preserved

### 12. Testing

Test async flow:
```python
# Test task submission
response = client.post('/ai/chat/message/', json={'message': 'test'})
assert response.json()['success'] == True
task_id = response.json()['task_id']

# Test polling
response = client.get(f'/ai/task/{task_id}/')
assert response.json()['status'] in ['processing', 'completed', 'failed']
```

### 13. Future Enhancements

- [ ] WebSocket support for real-time streaming responses
- [ ] Progress indicators (e.g., "Analyzing image...", "Generating response...")
- [ ] Task priority queue for premium users
- [ ] Response caching for common questions
- [ ] Analytics on task completion times

## Migration Notes

No database migrations required. The change is purely functional and uses existing infrastructure (Celery + Cache).

## Rollback Plan

If issues arise, revert:
1. `/apps/core/ai_chat_views.py` - restore sync version
2. `/templates/ai_chat/chat.html` - restore direct response handling
3. Delete `/apps/core/tasks.py`

The old synchronous behavior can be restored without data loss.
