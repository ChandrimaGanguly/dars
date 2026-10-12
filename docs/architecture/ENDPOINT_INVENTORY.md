# FastAPI Endpoint Inventory

**Complete list of all 12 REST endpoints implemented**

---

## 1. Health Check

### GET /health
**Tags:** System  
**Auth:** None (public)  
**Description:** Check system health (database + Claude API)

**Response 200:**
```json
{
  "status": "ok",
  "db": "ok", 
  "claude": "ok",
  "timestamp": "2026-01-28T10:00:00Z"
}
```

**Response 503:** Service unavailable
```json
{
  "status": "error",
  "db": "timeout",
  "claude": "ok",
  "timestamp": "2026-01-28T10:00:00Z"
}
```

---

## 2. Telegram Webhook

### POST /webhook
**Tags:** Telegram  
**Auth:** Bearer token (TODO)  
**Description:** Receive and process Telegram bot updates

**Request Body:**
```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 1,
    "date": 1643129200,
    "chat": {"id": 987654321, "type": "private"},
    "from": {
      "id": 987654321,
      "is_bot": false,
      "first_name": "Rajesh"
    },
    "text": "/start"
  }
}
```

**Response 200:**
```json
{
  "status": "ok",
  "message_id": 1
}
```

---

## 3. Get Practice Problems

### GET /practice
**Tags:** Student Practice  
**Auth:** X-Student-ID header (Telegram ID)  
**Description:** Get 5 daily practice problems

**Headers:**
- `X-Student-ID: 987654321` (required)

**Response 200:**
```json
{
  "session_id": 1,
  "problems": [
    {
      "problem_id": 1,
      "grade": 7,
      "topic": "Profit & Loss",
      "question_en": "A shopkeeper buys 15 mangoes for Rs. 300...",
      "question_bn": "একজন দোকানদার 15টি আম ₹300 এর জন্য ক্রয় করেন...",
      "difficulty": 1,
      "answer_type": "numeric"
    }
  ],
  "problem_count": 5,
  "expires_at": "2026-01-28T11:00:00Z"
}
```

---

## 4. Submit Answer

### POST /practice/{problem_id}/answer
**Tags:** Student Practice  
**Auth:** X-Student-ID header  
**Description:** Submit answer to a problem

**Path Parameters:**
- `problem_id` (int): Problem ID

**Headers:**
- `X-Student-ID: 987654321` (required)

**Request Body:**
```json
{
  "session_id": 1,
  "student_answer": "75",
  "time_spent_seconds": 45
}
```

**Response 200:**
```json
{
  "is_correct": true,
  "feedback_text": "Correct! Well done!",
  "next_problem_id": 2
}
```

---

## 5. Request Hint

### POST /practice/{problem_id}/hint
**Tags:** Student Practice  
**Auth:** X-Student-ID header  
**Description:** Request a Socratic hint (max 3 per problem)

**Path Parameters:**
- `problem_id` (int): Problem ID

**Headers:**
- `X-Student-ID: 987654321` (required)

**Request Body:**
```json
{
  "session_id": 1,
  "student_answer": "50",
  "hint_number": 1
}
```

**Response 200:**
```json
{
  "hint_text": "Think about the cost of each item first.",
  "hint_number": 1,
  "hints_remaining": 2
}
```

**Response 422:** Invalid hint number (must be 1-3)

---

## 6. Get Streak

### GET /streak
**Tags:** Student Engagement  
**Auth:** X-Student-ID header  
**Description:** Get student's streak information

**Headers:**
- `X-Student-ID: 987654321` (required)

**Response 200:**
```json
{
  "student_id": 1,
  "current_streak": 12,
  "longest_streak": 28,
  "last_practice_date": "2026-01-28T10:00:00Z",
  "milestones_achieved": [7, 14],
  "updated_at": "2026-01-28T10:00:00Z"
}
```

---

## 7. Get Student Profile

### GET /student/profile
**Tags:** Student  
**Auth:** X-Student-ID header  
**Description:** Get student's learning profile

**Headers:**
- `X-Student-ID: 987654321` (required)

**Response 200:**
```json
{
  "student_id": 1,
  "telegram_id": 987654321,
  "name": "Rajesh",
  "grade": 7,
  "language": "bn",
  "current_streak": 12,
  "longest_streak": 28,
  "avg_accuracy": 72.5,
  "last_practice": "2026-01-28T10:00:00Z",
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-01-28T10:00:00Z"
}
```

---

## 8. Update Student Profile

### PATCH /student/profile
**Tags:** Student  
**Auth:** X-Student-ID header  
**Description:** Update student preferences

**Headers:**
- `X-Student-ID: 987654321` (required)

**Request Body:**
```json
{
  "language": "en",
  "grade": 8
}
```

**Response 200:** Same as GET /student/profile

---

## 9. Get Admin Stats

### GET /admin/stats
**Tags:** Admin  
**Auth:** X-Admin-ID header  
**Description:** Get system statistics

**Headers:**
- `X-Admin-ID: 123456` (required)

**Response 200:**
```json
{
  "total_students": 50,
  "active_this_week": 42,
  "active_this_week_percent": 84.0,
  "avg_streak": 7.2,
  "avg_problems_per_session": 4.8,
  "total_sessions": 342,
  "timestamp": "2026-01-28T10:00:00Z"
}
```

---

## 10. List Students

### GET /admin/students
**Tags:** Admin  
**Auth:** X-Admin-ID header  
**Description:** List all students with pagination

**Headers:**
- `X-Admin-ID: 123456` (required)

**Query Parameters:**
- `grade` (int, optional): Filter by grade (6, 7, or 8)
- `page` (int, default=1): Page number
- `limit` (int, default=20): Items per page (max 100)

**Response 200:**
```json
{
  "students": [
    {
      "student_id": 1,
      "telegram_id": 987654321,
      "name": "Rajesh",
      "grade": 7,
      "language": "bn",
      "current_streak": 12,
      "longest_streak": 28,
      "avg_accuracy": 72.5,
      "last_practice": "2026-01-28T10:00:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

---

## 11. Get Cost Summary

### GET /admin/cost
**Tags:** Admin  
**Auth:** X-Admin-ID header  
**Description:** Get cost summary with budget alerts

**Headers:**
- `X-Admin-ID: 123456` (required)

**Query Parameters:**
- `period` (string, default="week"): Time period (day/week/month)

**Response 200:**
```json
{
  "period": "week",
  "total_cost": 1.23,
  "daily_average": 0.18,
  "projected_monthly": 7.80,
  "per_student_cost": 0.16,
  "claude_cost": 1.10,
  "infrastructure_cost": 0.13,
  "alert": true,
  "alert_message": "Over budget - exceeds $0.15/student/month",
  "timestamp": "2026-01-28T10:00:00Z"
}
```

---

## 12. Root Endpoint

### GET /
**Tags:** System  
**Auth:** None (public)  
**Description:** API information

**Response 200:**
```json
{
  "name": "Dars AI Tutoring Platform API",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs"
}
```

---

## OpenAPI Documentation

**Interactive documentation available at:**
- `/docs` - Swagger UI
- `/redoc` - ReDoc
- `/openapi.json` - OpenAPI 3.1.0 specification

---

## Authentication Summary

| Endpoint Type | Auth Method | Header Name | Example Value |
|--------------|-------------|-------------|---------------|
| Public | None | - | - |
| Telegram | Bearer Token | `Authorization` | `Bearer <token>` |
| Student | Header | `X-Student-ID` | `987654321` |
| Admin | Header | `X-Admin-ID` | `123456` |

---

## Error Responses

All endpoints return standard error format on failure:

```json
{
  "error": "validation_error",
  "message": "Invalid request data",
  "error_code": "ERR_VALIDATION",
  "details": {},
  "timestamp": "2026-01-28T10:00:00Z",
  "request_id": "abc123"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error
- `503` - Service Unavailable

---

**Implementation Status:** ✅ Complete  
**Last Updated:** 2026-01-28  
**Branch:** feature/fastapi-endpoints
