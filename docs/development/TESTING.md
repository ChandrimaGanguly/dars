# Testing & Code Quality Guide

Dars uses a multi-layered approach to ensure code quality: unit tests, integration tests, linting, and type checking.

## Quick Start

### 1. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Set Up Pre-commit Hooks

```bash
bash scripts/setup-hooks.sh
```

This installs and configures git hooks that run automatically before each commit.

### 3. Run Tests Locally

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# Specific test file
pytest tests/unit/test_example.py -v

# With coverage report
pytest --cov=src --cov-report=html
```

---

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures for all tests
├── unit/                 # Tests without external dependencies
│   ├── __init__.py
│   ├── test_example.py
│   ├── test_streaks.py
│   ├── test_problems.py
│   └── test_evaluator.py
└── integration/          # Tests requiring database/API
    ├── __init__.py
    ├── test_telegram_flow.py
    ├── test_practice_flow.py
    └── test_database.py
```

### Unit Tests (`tests/unit/`)

Fast tests that run in isolation with no external dependencies.

- **Streaks**: Streak calculation, milestone detection
- **Problems**: Problem selection, difficulty adaptation, filtering
- **Evaluator**: Answer checking, hint generation
- **Helpers**: Utility functions, formatters

**Mark with:** `@pytest.mark.unit`

### Integration Tests (`tests/integration/`)

Slower tests that use real database and API interactions.

- **Telegram flows**: Full /start → /practice → completion cycle
- **Database**: Student registration, session persistence, streak tracking
- **Claude API**: Hint generation, response evaluation (with mocking)

**Mark with:** `@pytest.mark.integration`

---

## Running Tests

### All tests
```bash
pytest
```

### Unit tests only (fast)
```bash
pytest -m unit
```

### Integration tests only
```bash
pytest -m integration
```

### Specific test file
```bash
pytest tests/unit/test_streaks.py
```

### Specific test class
```bash
pytest tests/unit/test_streaks.py::TestStreakCalculation
```

### Specific test
```bash
pytest tests/unit/test_streaks.py::TestStreakCalculation::test_streak_increments
```

### With verbose output
```bash
pytest -v
```

### With coverage report
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

The HTML report will be in `htmlcov/index.html`.

### Stop on first failure
```bash
pytest -x
```

### Only show failures
```bash
pytest --tb=short
```

---

## Code Quality Tools

### Black (Code Formatter)

Enforces consistent code style automatically.

```bash
# Format all Python files
black src tests

# Check formatting without changes
black --check src tests
```

### Ruff (Linter)

Catches potential bugs and style issues.

```bash
# Lint all Python files
ruff check src tests

# Auto-fix violations where possible
ruff check --fix src tests
```

### MyPy (Type Checker)

Catches type errors statically.

```bash
# Type check all files
mypy src

# Type check specific file
mypy src/models.py
```

### All Tools Together

```bash
# Format + Lint + Type Check
black src tests && ruff check --fix src tests && mypy src
```

---

## Pre-commit Hooks

Hooks run automatically when you commit, preventing bad code from being committed.

### What Hooks Run

| Hook | Purpose | Fix? |
|------|---------|------|
| black | Format code | Yes |
| ruff | Lint and format | Yes |
| mypy | Type check | No |
| pytest | Validate tests exist | No |
| YAML/JSON | Validate config files | No |
| Merge conflicts | Detect merge conflict markers | No |

### Manual Hook Execution

```bash
# Run all hooks on all files (useful before pushing)
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks for a commit (not recommended!)
git commit --no-verify
```

### Troubleshooting Hooks

**Hook failures on commit:**
- Fix suggested errors
- Run `git add .` again
- Commit again

**Hooks modifying files:**
- Review changes: `git diff`
- Stage changes: `git add .`
- Commit: `git commit -m "..."`

**Slow hooks:**
- Type checking can be slow on large codebases
- Integration tests are skipped in pre-commit (run `pytest` instead)

---

## Code Coverage

We target >70% coverage on core modules.

### Generate Coverage Report

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Coverage by Module

```bash
pytest --cov=src --cov-report=term-missing
```

Shows lines not covered by tests.

### Fail if Below Threshold

```bash
pytest --cov=src --cov-fail-under=70
```

---

## Test Fixtures

Common fixtures are in `tests/conftest.py`.

### Database Fixtures

```python
def test_something(test_db_session):
    # test_db_session is a fresh database for this test
    pass
```

### Telegram Fixtures

```python
def test_telegram_update(mock_telegram_update):
    # mock_telegram_update is a sample Telegram message
    update = mock_telegram_update
    assert update["message"]["text"] == "/start"
```

### API Fixtures

```python
def test_claude_response(mock_claude_response):
    # mock_claude_response is a sample Claude API response
    response = mock_claude_response
    assert response["model"] == "claude-3-haiku-20240307"
```

### Environment Variables

```python
def test_config(env_vars):
    # env_vars are set for this test (TELEGRAM_BOT_TOKEN, etc.)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    assert token == "test_token_123456:ABCDEFG"
```

---

## Writing Tests

### Unit Test Template

```python
import pytest

class TestStreakCalculation:
    """Tests for streak logic."""

    def test_streak_increments(self) -> None:
        """Should increment streak on consecutive days."""
        # Arrange
        streak = Streak()

        # Act
        result = streak.increment()

        # Assert
        assert result == 1
```

### Integration Test Template

```python
import pytest

@pytest.mark.integration
class TestPracticeFlow:
    """Tests for full practice experience."""

    def test_practice_session(self, test_db_session) -> None:
        """Should complete 5-problem session."""
        # Setup
        student = Student(telegram_id=123)
        test_db_session.add(student)
        test_db_session.commit()

        # Act
        session = practice.start(student.id, test_db_session)
        for _ in range(5):
            practice.answer_question(session.id, "5")

        # Assert
        assert session.completed_at is not None
```

### Async Test Template

```python
import pytest

@pytest.mark.asyncio
async def test_telegram_message(mock_telegram_update) -> None:
    """Test async Telegram handler."""
    # Arrange
    update = mock_telegram_update

    # Act
    response = await telegram.handle_message(update)

    # Assert
    assert response.status_code == 200
```

---

## Type Hints

All new code should include type hints for better IDE support and type checking.

### Good Type Hints

```python
from typing import Optional, List

def calculate_streak(student_id: int, sessions: List[Session]) -> int:
    """Calculate current streak for a student."""
    if not sessions:
        return 0
    return len(sessions)

def find_student(telegram_id: int) -> Optional[Student]:
    """Find student or return None."""
    return db.query(Student).filter_by(telegram_id=telegram_id).first()
```

### Async Functions

```python
async def handle_telegram_message(update: Update) -> Response:
    """Handle incoming Telegram message."""
    student = await db.get_student(update.effective_user.id)
    return Response(status=200)
```

---

## CI/CD Integration

Tests run automatically in CI/CD on every push.

### GitHub Actions

Pre-configured workflows in `.github/workflows/`:
- `test.yml` - Run tests on all PRs
- `coverage.yml` - Report coverage on PRs

No manual setup needed; workflows run automatically.

---

## Troubleshooting

### Tests Fail Locally But Pass in CI

- Check Python version: `python --version` (should be 3.11+)
- Ensure you're in the right environment
- Run full test suite: `pytest --tb=short`

### Type Checking Errors

- Check that all function parameters have type hints
- Check that all return types are annotated
- Run `mypy src --strict` to catch all errors

### Hook Failures

- Run `pre-commit run --all-files` to fix all issues
- Check `.pre-commit-config.yaml` for hook configuration

### Import Errors

- Ensure you've run: `pip install -e ".[dev]"`
- Check that `src/` files exist (they don't yet, will be created in TASK-001)

---

## Reference

- [Pytest Documentation](https://docs.pytest.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
