# Database Layer Quick Start Guide

## 🚀 Quick Commands

### Setup Database
```bash
# 1. Set environment variable
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dars_db"

# 2. Run migrations
alembic upgrade head

# 3. Verify connection (Python)
python -c "import asyncio; from src.database import check_connection; print(asyncio.run(check_connection()))"
```

### Run Tests
```bash
# Run all model tests
pytest tests/unit/test_models.py -v

# Run with coverage
pytest tests/unit/test_models.py --cov=src/models

# Run verification script
python verify_database.py
```

### Code Quality
```bash
# Format code
black src/

# Check linting
ruff check src/

# Check types
mypy src/database.py src/models/
```

---

## 📦 Import Models

```python
# Import all models
from src.models import Student, Problem, Session, Response, Streak, CostRecord

# Import database session
from src.database import get_session

# Use in FastAPI
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/students/{student_id}")
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_session)
):
    student = await db.get(Student, student_id)
    return student
```

---

## 🔍 Common Queries

### Create Student
```python
from src.models import Student

async with get_session() as db:
    student = Student(
        telegram_id=123456789,
        name="Ali Rahman",
        grade=7,
        language="bn"
    )
    db.add(student)
    await db.commit()
```

### Find Student by Telegram ID
```python
from sqlalchemy import select

async with get_session() as db:
    stmt = select(Student).where(Student.telegram_id == 123456789)
    result = await db.execute(stmt)
    student = result.scalar_one_or_none()
```

### Create Practice Session
```python
from datetime import datetime, timedelta, timezone
from src.models import Session

async with get_session() as db:
    now = datetime.now(timezone.utc)
    session = Session(
        student_id=student_id,
        date=now,
        status="in_progress",
        problem_ids=[1, 2, 3, 4, 5],
        expires_at=now + timedelta(minutes=30),
    )
    db.add(session)
    await db.commit()
```

### Track Cost
```python
from src.models import CostRecord

async with get_session() as db:
    cost = CostRecord(
        student_id=1,
        session_id=1,
        operation="hint_generation",
        api_provider="claude",
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.0015,
    )
    db.add(cost)
    await db.commit()
```

### Update Streak
```python
from src.models import Streak

async with get_session() as db:
    streak = await db.get(Streak, student_id=1)
    streak.current_streak += 1
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak
    streak.add_milestone(7)  # Add milestone if reached
    await db.commit()
```

---

## 📊 Schema Overview

```
students
├── student_id (PK)
├── telegram_id (UNIQUE)
├── name
├── grade (6, 7, 8)
└── language (bn, en)

problems
├── problem_id (PK)
├── grade (6, 7, 8)
├── topic
├── question_en / question_bn
├── answer
├── hints (JSON)
└── difficulty (1, 2, 3)

sessions
├── session_id (PK)
├── student_id (FK)
├── date
├── status (in_progress, completed, abandoned)
├── problem_ids (JSON array)
└── expires_at

responses
├── response_id (PK)
├── session_id (FK)
├── problem_id (FK)
├── student_answer
├── is_correct
└── hints_used

streaks
├── student_id (PK/FK)
├── current_streak
├── longest_streak
└── milestones_achieved (JSON)

cost_records
├── cost_id (PK)
├── student_id (FK)
├── operation
├── api_provider
└── cost_usd
```

---

## 🔧 Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history
```

---

## 📝 Files Created

**Models** (1,248 total lines):
- `src/models/base.py` - Base model (60 lines)
- `src/models/student.py` - Student model (114 lines)
- `src/models/problem.py` - Problem + Hint (180 lines)
- `src/models/session.py` - Session model (163 lines)
- `src/models/response.py` - Response model (150 lines)
- `src/models/streak.py` - Streak model (125 lines)
- `src/models/cost_record.py` - CostRecord (140 lines)
- `src/models/__init__.py` - Exports (27 lines)

**Database**:
- `src/database.py` - Connection (195 lines)

**Migrations**:
- `alembic/env.py` - Alembic config (async)
- `alembic/versions/47eebe03a353_*.py` - Initial migration

**Tests**:
- `tests/unit/test_models.py` - 14 unit tests

**Documentation**:
- `DATABASE_SCHEMA.md` - Complete reference
- `DELIVERY_REPORT_DATABASE.md` - Delivery report
- `QUICKSTART_DATABASE.md` - This file

---

## ❓ Troubleshooting

### "DATABASE_URL not set"
```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"
```

### "Connection refused"
- Ensure PostgreSQL is running
- Check host/port in DATABASE_URL
- For Railway, use provided DATABASE_URL

### "asyncpg not installed"
```bash
pip install asyncpg
```

### Migration fails with "revision not found"
```bash
# Check current state
alembic current

# If empty, run initial migration
alembic upgrade head
```

---

## 📚 Documentation

- **Full Schema**: See `DATABASE_SCHEMA.md`
- **Delivery Report**: See `DELIVERY_REPORT_DATABASE.md`
- **API Architecture**: See `API_ARCHITECTURE.md` Part 3
- **Requirements**: See `REQUIREMENTS.md` REQ-017

---

**Built by**: Maryam (Stream A - Backend Infrastructure)
**Status**: Production Ready ✅
**Last Updated**: 2026-01-28
