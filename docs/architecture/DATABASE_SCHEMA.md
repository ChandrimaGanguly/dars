# Database Schema Documentation

## Overview

This document describes the database schema for the Dars AI Tutoring Platform. The schema uses PostgreSQL with async SQLAlchemy 2.0+ and Alembic migrations.

## Architecture

- **ORM**: SQLAlchemy 2.0+ with async support (asyncpg driver)
- **Migrations**: Alembic with async configuration
- **Type Safety**: Full MyPy strict mode compliance
- **Connection Pooling**: Configured for production with Railway

## Database Models

### 1. Student Model

**Table**: `students`

Represents learners in the system with Telegram authentication.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `student_id` | INTEGER | PRIMARY KEY, AUTO | Unique student identifier |
| `telegram_id` | BIGINT | UNIQUE, NOT NULL, INDEXED | Telegram user ID (authentication) |
| `name` | VARCHAR(100) | NOT NULL | Student's display name |
| `grade` | INTEGER | NOT NULL, CHECK (6,7,8) | Grade level |
| `language` | VARCHAR(2) | NOT NULL, CHECK ('bn','en'), DEFAULT 'bn' | Preferred language |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Registration timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp (UTC) |

**Relationships**:
- One-to-many with `Session`
- One-to-one with `Streak`
- One-to-many with `CostRecord`

**Indexes**:
- `idx_students_telegram_id` on `telegram_id`
- `idx_students_grade` on `grade`

---

### 2. Problem Model

**Table**: `problems`

Represents math problems in the content library (280 problems total).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `problem_id` | INTEGER | PRIMARY KEY, AUTO | Unique problem identifier |
| `grade` | INTEGER | NOT NULL, CHECK (6,7,8) | Target grade level |
| `topic` | VARCHAR(100) | NOT NULL | Topic (e.g., "Profit & Loss") |
| `subtopic` | VARCHAR(100) | NULL | Optional subtopic |
| `question_en` | TEXT | NOT NULL | Question in English |
| `question_bn` | TEXT | NOT NULL | Question in Bengali |
| `answer` | VARCHAR(500) | NOT NULL | Correct answer |
| `hints` | JSON | NOT NULL | Array of 3 hints (JSON format) |
| `difficulty` | INTEGER | NOT NULL, CHECK (1,2,3) | Difficulty level |
| `estimated_time_minutes` | INTEGER | NOT NULL, DEFAULT 5 | Expected solve time |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp (UTC) |

**Hint JSON Structure**:
```json
[
  {
    "hint_number": 1,
    "text_en": "English hint",
    "text_bn": "Bengali hint",
    "is_ai_generated": false
  },
  ...
]
```

**Indexes**:
- `idx_problems_grade_topic` on `(grade, topic)` - composite index for problem selection
- `idx_problems_difficulty` on `difficulty`

---

### 3. Session Model

**Table**: `sessions`

Represents daily practice sessions (5 problems per session).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `session_id` | INTEGER | PRIMARY KEY, AUTO | Unique session identifier |
| `student_id` | INTEGER | FOREIGN KEY (students), NOT NULL | Session owner |
| `date` | TIMESTAMP | NOT NULL | Session date (UTC) |
| `status` | ENUM | NOT NULL, DEFAULT 'in_progress' | Session state |
| `problem_ids` | JSON | NOT NULL | Array of 5 problem IDs |
| `completed_at` | TIMESTAMP | NULL | Completion timestamp (UTC) |
| `expires_at` | TIMESTAMP | NOT NULL | Expiration time (30 min after start) |
| `total_time_seconds` | INTEGER | NOT NULL, DEFAULT 0 | Total time spent |
| `problems_correct` | INTEGER | NOT NULL, DEFAULT 0, CHECK (0-5) | Count of correct answers |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp (UTC) |

**Status ENUM**: `in_progress`, `completed`, `abandoned`

**Relationships**:
- Many-to-one with `Student`
- One-to-many with `Response`

**Indexes**:
- `idx_sessions_student_created` on `(student_id, created_at)` - for listing sessions
- `idx_sessions_status` on `status`
- `idx_sessions_date` on `date`

---

### 4. Response Model

**Table**: `responses`

Tracks student answers to individual problems within sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `response_id` | INTEGER | PRIMARY KEY, AUTO | Unique response identifier |
| `session_id` | INTEGER | FOREIGN KEY (sessions), NOT NULL | Parent session |
| `problem_id` | INTEGER | FOREIGN KEY (problems), NOT NULL | Problem answered |
| `student_answer` | VARCHAR(500) | NOT NULL | Student's submitted answer |
| `is_correct` | BOOLEAN | NOT NULL | Whether answer was correct |
| `time_spent_seconds` | INTEGER | NOT NULL, DEFAULT 0 | Time spent on problem |
| `hints_used` | INTEGER | NOT NULL, DEFAULT 0, CHECK (0-3) | Number of hints requested |
| `hints_viewed` | JSON | NOT NULL, DEFAULT [] | Array of viewed hints |
| `evaluated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Evaluation timestamp (UTC) |
| `confidence_level` | ENUM | NOT NULL, DEFAULT 'medium' | Confidence level |

**Confidence ENUM**: `low`, `medium`, `high`

**Relationships**:
- Many-to-one with `Session`
- Many-to-one with `Problem` (informational)

**Indexes**:
- `idx_responses_session` on `session_id`
- `idx_responses_problem` on `problem_id`
- `idx_responses_correctness` on `is_correct`

---

### 5. Streak Model

**Table**: `streaks`

Tracks daily practice habits and milestones.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `student_id` | INTEGER | PRIMARY KEY, FOREIGN KEY (students) | Student this streak belongs to |
| `current_streak` | INTEGER | NOT NULL, DEFAULT 0 | Current consecutive days |
| `longest_streak` | INTEGER | NOT NULL, DEFAULT 0 | Longest streak achieved |
| `last_practice_date` | DATE | NULL | Date of last practice |
| `milestones_achieved` | JSON | NOT NULL, DEFAULT [] | Milestone days reached |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation timestamp (UTC) |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp (UTC) |

**Constraints**:
- CHECK: `longest_streak >= current_streak`
- CHECK: `current_streak >= 0`
- CHECK: `longest_streak >= 0`

**Milestones**: `[7, 14, 30, 60, 90, 180, 365]` days

**Relationships**:
- One-to-one with `Student`

**Indexes**:
- `idx_streaks_current` on `current_streak`

---

### 6. CostRecord Model

**Table**: `cost_records`

Tracks API usage costs for business model validation (target: <$0.10/student/month).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `cost_id` | INTEGER | PRIMARY KEY, AUTO | Unique cost record identifier |
| `student_id` | INTEGER | FOREIGN KEY (students), NOT NULL | Student who triggered cost |
| `session_id` | INTEGER | FOREIGN KEY (sessions), NULL | Optional session reference |
| `operation` | ENUM | NOT NULL | Type of operation |
| `api_provider` | ENUM | NOT NULL | API provider used |
| `input_tokens` | INTEGER | NULL | Input tokens (Claude API) |
| `output_tokens` | INTEGER | NULL | Output tokens (Claude API) |
| `cost_usd` | FLOAT | NOT NULL, CHECK >= 0 | Cost in USD |
| `recorded_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Recording timestamp (UTC) |

**Operation ENUM**: `hint_generation`, `answer_evaluation`
**Provider ENUM**: `claude`, `twilio`

**Relationships**:
- Many-to-one with `Student`
- Many-to-one with `Session` (optional)

**Indexes**:
- `idx_cost_records_student` on `student_id`
- `idx_cost_records_session` on `session_id`
- `idx_cost_records_recorded` on `recorded_at`
- `idx_cost_records_operation` on `operation`

---

## Database Connection Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname

# Optional (for development)
DATABASE_ECHO=false  # Log all SQL statements
DATABASE_POOL_SIZE=5  # Connection pool size
DATABASE_MAX_OVERFLOW=10  # Max overflow connections
```

### Connection Pool Settings

**Production (Railway)**:
- Pool size: 5
- Max overflow: 10
- Pool class: `QueuePool`
- Pool pre-ping: Enabled

**Testing**:
- Pool class: `NullPool` (no pooling)

---

## Migrations

### Alembic Configuration

**Location**: `alembic/versions/`

**Run Migrations**:
```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Initial Migration

**File**: `47eebe03a353_initial_schema_with_all_models.py`

Creates all 6 tables with indexes, constraints, and foreign keys.

---

## Usage Examples

### Creating a Session

```python
from src.database import get_session
from src.models import Student, Session
from datetime import datetime, timedelta, timezone

async with get_session() as db:
    # Find student
    student = await db.get(Student, student_id=1)
    
    # Create session
    now = datetime.now(timezone.utc)
    session = Session(
        student_id=student.student_id,
        date=now,
        status="in_progress",
        problem_ids=[1, 2, 3, 4, 5],
        expires_at=now + timedelta(minutes=30),
    )
    
    db.add(session)
    await db.commit()
```

### Querying Problems

```python
from sqlalchemy import select
from src.models import Problem

async with get_session() as db:
    # Get problems for grade 7, topic "Profit & Loss", difficulty 2
    stmt = select(Problem).where(
        Problem.grade == 7,
        Problem.topic == "Profit & Loss",
        Problem.difficulty == 2
    )
    result = await db.execute(stmt)
    problems = result.scalars().all()
```

### Updating Streaks

```python
from src.models import Streak
from datetime import date

async with get_session() as db:
    streak = await db.get(Streak, student_id=1)
    
    # Increment streak
    streak.current_streak += 1
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak
    
    streak.last_practice_date = date.today()
    
    # Add milestone if reached
    if streak.current_streak == 7:
        streak.add_milestone(7)
    
    await db.commit()
```

---

## Database Handoff

### For Jodha (API Development)

**Import models in your endpoints**:
```python
from src.database import get_session
from src.models import Student, Session, Problem, Response
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.post("/practice/start")
async def start_practice(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    # Use db session here
    student = await db.get(Student, student_id)
    ...
```

**Connection string format**: Set `DATABASE_URL` env var
- Local: `postgresql+asyncpg://user:pass@localhost:5432/dars_db`
- Railway: Provided by Railway (auto-configured)

### For Noor (Security/Logging)

**Database connection available at**:
```python
from src.database import get_engine, check_connection

# Health check
is_connected = await check_connection()

# Get engine for middleware
engine = get_engine()
```

**Cost tracking integration**:
```python
from src.models import CostRecord

async def log_claude_call(
    student_id: int,
    session_id: int,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float
):
    record = CostRecord(
        student_id=student_id,
        session_id=session_id,
        operation="hint_generation",
        api_provider="claude",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
    )
    db.add(record)
    await db.commit()
```

---

## Testing

**Run unit tests**:
```bash
pytest tests/unit/test_models.py -v
```

**Coverage**: 14 test cases covering all models

**Test database**: Not required for unit tests (uses model validation only)

---

## Validation Status

- [x] All 6 models created
- [x] Alembic initial migration created
- [x] Database connection module implemented
- [x] Async session management configured
- [x] All indexes added
- [x] Unit tests passing (14/14)
- [x] Black formatting passed
- [x] Ruff linting passed
- [x] MyPy strict mode passed

---

## Next Steps

1. **Set DATABASE_URL** environment variable
2. **Run migrations**: `alembic upgrade head`
3. **Import models** in API endpoints
4. **Test database connection** with `check_connection()`
5. **Begin integrating** with FastAPI endpoints

---

**Built by**: Maryam (Backend Expert, Stream A)
**Date**: 2026-01-28
**Phase**: Phase 1 - Backend Foundation
**Status**: Complete ✅
