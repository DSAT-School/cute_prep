# API Reference

## Overview

The Practice Portal API is a RESTful API built with Django REST Framework. All endpoints return JSON responses and follow standard HTTP conventions.

## Base URL

```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

## Authentication

The API uses session-based authentication by default. Token authentication can be added as needed.

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

### Logout
```http
POST /api/auth/logout
```

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Health Check

### Check System Health

```http
GET /api/health/
```

**Response 200 OK**
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected"
}
```

**Response 503 Service Unavailable**
```json
{
  "status": "unhealthy",
  "database": "error: connection refused",
  "cache": "disconnected"
}
```

## Users

### List Users

```http
GET /api/users/
Authorization: Required
```

**Query Parameters**
- `page` (integer): Page number for pagination
- `page_size` (integer): Number of results per page (max 100)

**Response 200 OK**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Create User

```http
POST /api/users/
Content-Type: application/json
```

**Request Body**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response 201 Created**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Response 400 Bad Request**
```json
{
  "username": ["This field is required."],
  "password": ["Password fields didn't match."]
}
```

### Get Current User

```http
GET /api/users/me/
Authorization: Required
```

**Response 200 OK**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Get User by ID

```http
GET /api/users/{id}/
Authorization: Required
```

**Path Parameters**
- `id` (UUID): User ID

**Response 200 OK**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Response 404 Not Found**
```json
{
  "detail": "Not found."
}
```

### Update User

```http
PATCH /api/users/{id}/
Authorization: Required
Content-Type: application/json
```

**Path Parameters**
- `id` (UUID): User ID

**Request Body** (all fields optional for PATCH)
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane@example.com"
}
```

**Response 200 OK**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "email": "jane@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "full_name": "Jane Smith",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-02T00:00:00Z"
}
```

### Delete User

```http
DELETE /api/users/{id}/
Authorization: Required
```

**Path Parameters**
- `id` (UUID): User ID

**Response 204 No Content**

## Pagination

All list endpoints support pagination.

### Default Pagination
- Page size: 20 items
- Max page size: 100 items

### Custom Pagination
```http
GET /api/users/?page=2&page_size=50
```

### Response Format
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/users/?page=3",
  "previous": "http://localhost:8000/api/users/?page=1",
  "results": [...]
}
```

## Rate Limiting

API endpoints are rate-limited to prevent abuse.

### Limits
- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded
**Response 429 Too Many Requests**
```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

## Filtering

List endpoints support filtering via query parameters.

### Example
```http
GET /api/users/?is_active=true&created_at__gte=2024-01-01
```

### Common Filter Operators
- `field=value`: Exact match
- `field__icontains=value`: Case-insensitive contains
- `field__gte=value`: Greater than or equal
- `field__lte=value`: Less than or equal
- `field__in=val1,val2`: In list

## Ordering

List endpoints support ordering via the `ordering` parameter.

### Example
```http
GET /api/users/?ordering=-created_at
```

### Ordering Options
- `ordering=field`: Ascending
- `ordering=-field`: Descending
- `ordering=field1,-field2`: Multiple fields

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

### Field Validation Errors
```json
{
  "field_name": [
    "Error message 1",
    "Error message 2"
  ]
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `invalid` | Invalid input |
| `required` | Required field missing |
| `unique` | Value must be unique |
| `not_found` | Resource not found |
| `permission_denied` | Insufficient permissions |
| `throttled` | Rate limit exceeded |

## Versioning

The API uses URL versioning (optional for future versions).

```http
GET /api/v1/users/
GET /api/v2/users/
```

Current version: v1 (default)

## CORS

CORS is configured for the following origins:
- Development: All origins allowed
- Production: Configured origins only

## Testing

### Using cURL

```bash
# Create user
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'

# Get user
curl http://localhost:8000/api/users/me/ \
  -H "Authorization: Token your-token-here"
```

### Using Python Requests

```python
import requests

# Create user
response = requests.post(
    "http://localhost:8000/api/users/",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123"
    }
)
print(response.json())

# Get user
response = requests.get(
    "http://localhost:8000/api/users/me/",
    headers={"Authorization": "Token your-token-here"}
)
print(response.json())
```

## WebSocket Support (Future)

WebSocket endpoints will be available at:
```
ws://localhost:8000/ws/
```

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial API release
- User management endpoints
- Health check endpoint
- Session authentication
- Rate limiting

## Support

For API support, please contact:
- Email: api@practiceportal.com
- Documentation: https://docs.practiceportal.com
- GitHub Issues: https://github.com/your-org/practice-portal/issues
