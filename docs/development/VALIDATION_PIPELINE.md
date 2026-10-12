# End-to-End Validation Pipeline

This document describes the comprehensive validation pipeline that all code must pass before being committed to the repository. The pipeline is designed to catch issues early and ensure consistent code quality.

## Overview

The validation pipeline consists of **7 sequential stages** that run automatically:

```
┌─────────────────────────────────────────────────────────────┐
│         END-TO-END VALIDATION PIPELINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  STAGE 1: Code Formatting (Black)                           │
│  └─ Ensures consistent code style                           │
│                                                              │
│  STAGE 2: Linting (Ruff)                                    │
│  └─ Catches common errors and style issues                  │
│                                                              │
│  STAGE 3: Type Checking (MyPy)                              │
│  └─ Catches type errors statically                          │
│                                                              │
│  STAGE 4: Unit Tests                                        │
│  └─ Tests individual components in isolation                │
│                                                              │
│  STAGE 5: Integration Tests (Optional - slow)               │
│  └─ Tests components working together                       │
│                                                              │
│  STAGE 6: Test Coverage                                     │
│  └─ Enforces minimum 70% coverage                           │
│                                                              │
│  STAGE 7: Git Status                                        │
│  └─ Detects sensitive files, checks for changes             │
│                                                              │
│  ✓ ALL PASSED → Commit allowed                              │
│  ✗ ANY FAILED → Commit blocked                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Running the Pipeline

### Before Committing (Manual Validation)

```bash
# Run full pipeline (includes slow integration tests)
bash scripts/validate.sh

# Run pipeline and auto-fix formatting/linting issues
bash scripts/validate.sh --fix

# Run pipeline without slow integration tests
bash scripts/validate.sh --skip-slow

# Run pipeline with verbose output
bash scripts/validate.sh -v
```

### On Commit (Automatic via Git Hook)

```bash
# Just commit normally
git commit -m "Your message"

# The pre-commit hook automatically runs:
# 1. Code formatting check (black)
# 2. Linting check (ruff)
# 3. Type checking (mypy)
# 4. Unit tests
# 5. Coverage check (≥70%)
# 6. Git status check
#
# (Integration tests are skipped in pre-commit to save time)
#
# If all pass → Commit succeeds
# If any fail → Commit blocked, fix issues, retry
```

### In CI/CD (GitHub Actions)

```yaml
# Automatically runs on:
# - Every push to main/master/develop
# - Every pull request

# Runs full pipeline including integration tests
# Reports coverage to Codecov
# Fails the build if validation fails
```

## Installation

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Install Git Hooks

```bash
bash scripts/install-git-hooks.sh
```

This sets up:
- **pre-commit**: Runs validation pipeline before commits
- **prepare-commit-msg**: Adds branch name to commit messages

### 3. Verify Installation

```bash
# Check hooks are installed
ls -la .git/hooks/ | grep pre-commit

# Test by running validation manually
bash scripts/validate.sh
```

## Detailed Stages

### Stage 1: Code Formatting (Black)

**Purpose:** Enforce consistent code style automatically

**What it checks:**
- Line length (100 characters max)
- String quote style
- Whitespace and indentation
- Operator spacing

**If it fails:**
```bash
# Auto-fix all formatting
bash scripts/validate.sh --fix

# Or manually
black src tests
```

**Config:** `pyproject.toml` → `[tool.black]`

---

### Stage 2: Linting (Ruff)

**Purpose:** Catch potential bugs and code style violations

**What it checks:**
- Unused imports
- Undefined names
- Type confusion
- Complexity issues
- Best practices

**If it fails:**
```bash
# Auto-fix most issues
bash scripts/validate.sh --fix

# Or manually
ruff check --fix src tests
```

**Config:** `pyproject.toml` → `[tool.ruff]`

---

### Stage 3: Type Checking (MyPy)

**Purpose:** Catch type errors before runtime (strict mode)

**What it checks:**
- Function parameter types
- Return type annotations
- Type mismatches
- Missing type hints

**If it fails:**
```bash
# Run and see detailed errors
mypy src

# Verbose output with line numbers
mypy src --show-error-context
```

**Config:** `pyproject.toml` → `[tool.mypy]`

**Requirements:**
- ALL functions must have type hints
- ALL return types must be annotated
- MyPy must pass with `--strict` mode

---

### Stage 4: Unit Tests

**Purpose:** Test individual functions and classes

**What it checks:**
- Logic correctness
- Edge cases
- Error handling

**If it fails:**
```bash
# Run tests with verbose output
pytest tests/unit -v

# Run specific test
pytest tests/unit/test_streaks.py -v

# Run specific test class
pytest tests/unit/test_streaks.py::TestStreakCalculation -v
```

**Markers:**
```python
@pytest.mark.unit      # Fast, no external deps
@pytest.mark.slow      # Slow tests (skip by default)
@pytest.mark.asyncio   # Async tests
```

**Config:** `pytest.ini` and `pyproject.toml` → `[tool.pytest.ini_options]`

---

### Stage 5: Integration Tests

**Purpose:** Test components working together (database, API, etc.)

**What it checks:**
- Full user flows
- Database persistence
- API interactions
- Service integration

**If it fails:**
```bash
# Run integration tests with verbose output
pytest tests/integration -v

# Run specific integration test
pytest tests/integration/test_telegram_flow.py -v
```

**Note:** Skipped during pre-commit (too slow). Run manually before pushing:
```bash
pytest tests/integration
```

**Marker:**
```python
@pytest.mark.integration  # Requires external services
```

---

### Stage 6: Test Coverage

**Purpose:** Ensure minimum code coverage (70% overall)

**What it checks:**
- Percentage of code covered by tests
- Which lines are not tested
- Coverage by module

**If it fails:**
```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open report
open htmlcov/index.html

# See coverage by line
pytest --cov=src --cov-report=term-missing
```

**Config:** `pyproject.toml` → `[tool.pytest.ini_options]` (cov-fail-under=70)

---

### Stage 7: Git Status

**Purpose:** Prevent accidentally committing sensitive files

**What it checks:**
- No untracked `.env` files
- No untracked `secrets/` files
- No merge conflict markers
- No large binary files

**If it fails:**
```bash
# Check git status
git status

# Add to .gitignore
echo "sensitive-file" >> .gitignore

# Or remove untracked files
git clean -fd
```

## Exit Codes

The validation script uses exit codes to indicate which stages failed:

| Code | Stage | Fix |
|------|-------|-----|
| 0 | ✓ All passed | Commit allowed |
| 1 | Formatting | `bash scripts/validate.sh --fix` |
| 2 | Linting | `bash scripts/validate.sh --fix` |
| 4 | Type checking | `mypy src` |
| 8 | Tests | `pytest -v` |
| 16 | Coverage | `pytest --cov=src` |

**Combined codes:** Exit code is sum of failed stages. E.g., formatting + linting = 3.

## Workflow: For Developers

### Before Committing

```bash
# 1. Make your changes
# 2. Run validation
bash scripts/validate.sh

# 3. If validation fails, fix issues
bash scripts/validate.sh --fix    # Auto-fixes formatting & linting
mypy src                          # Check type errors manually
pytest tests/unit -v              # Fix failing tests

# 4. Once validation passes, commit
git add .
git commit -m "feat: your feature"

# 5. Pre-commit hook runs automatically
# If it passes → commit succeeds
# If it fails → commit blocked, fix and retry
```

### If Pre-Commit Hook Blocks Commit

```bash
# See what failed
bash scripts/validate.sh -v

# Fix issues
bash scripts/validate.sh --fix    # For formatting/linting
mypy src                          # For type errors
pytest tests/unit -v              # For test failures

# Stage and commit again
git add .
git commit -m "feat: your feature"
```

### To Bypass Validation (NOT RECOMMENDED)

```bash
# Only in emergencies!
git commit --no-verify

# But then you must run full validation manually:
bash scripts/validate.sh --verbose
```

## Workflow: For Autonomous Agents

When an autonomous agent works on this codebase, it MUST:

1. **Before writing code:**
   ```bash
   bash scripts/validate.sh
   # Verify the pipeline is working
   ```

2. **While writing code:**
   - Include type hints on all functions
   - Write tests as you code (TDD approach)
   - Keep functions small and testable

3. **Before committing:**
   ```bash
   bash scripts/validate.sh --fix
   # This auto-fixes 90% of issues
   ```

4. **If validation fails:**
   ```bash
   # Run verbose to see what failed
   bash scripts/validate.sh -v

   # Fix type errors
   mypy src

   # Fix failing tests
   pytest tests/unit -v
   ```

5. **After all checks pass:**
   ```bash
   git add .
   git commit -m "feat: description"
   # Pre-commit hook runs automatically
   ```

## Checklist for Code Review

When reviewing pull requests, the CI/CD pipeline MUST:

- [ ] Stage 1: Black formatting passed
- [ ] Stage 2: Ruff linting passed
- [ ] Stage 3: MyPy type checking passed
- [ ] Stage 4: Unit tests passed
- [ ] Stage 5: Integration tests passed
- [ ] Stage 6: Coverage ≥70%
- [ ] Stage 7: No sensitive files

If any stage fails, the PR cannot be merged.

## Common Issues & Solutions

### "Code formatting issues found"

```bash
# Auto-fix
bash scripts/validate.sh --fix
git add .
git commit -m "style: fix formatting"
```

### "Type errors found"

```bash
# Check what's wrong
mypy src

# Example error: Missing type hint
# Add type hints:
def my_function(x: int, y: int) -> int:
    return x + y
```

### "Unit tests failed"

```bash
# Run tests in verbose mode
pytest tests/unit -v

# Fix the test failures
# Then run again
pytest tests/unit -v
```

### "Coverage below 70%"

```bash
# See which lines aren't covered
pytest --cov=src --cov-report=term-missing

# Write tests for uncovered lines
# Then re-run
pytest --cov=src
```

### "Pre-commit hook blocks commit"

```bash
# Check what failed
bash scripts/validate.sh -v

# Fix and retry
bash scripts/validate.sh --fix
git add .
git commit
```

## Performance

### Pipeline Timing

| Stage | Time |
|-------|------|
| Formatting (black) | ~1s |
| Linting (ruff) | ~1s |
| Type checking (mypy) | ~3-5s |
| Unit tests | ~5-10s |
| Coverage check | ~10-15s |
| **Total (no integration)** | **~20-30s** |
| Integration tests | ~30-60s |
| **Total (with integration)** | **~50-90s** |

### Optimization Tips

```bash
# Skip slow integration tests in pre-commit (default)
bash scripts/validate.sh --skip-slow

# Run validation in parallel (future improvement)
# For now, stages run sequentially

# Cache test results between runs (pytest feature)
# Automatically used by pytest-cache plugin
```

## CI/CD Integration

### GitHub Actions Workflow

The workflow in `.github/workflows/validation.yml` automatically:

1. **On every push to main/master/develop:**
   - Runs full validation pipeline
   - Uploads coverage to Codecov
   - Fails build if validation fails

2. **On every pull request:**
   - Runs full validation pipeline
   - Reports results in PR checks
   - Prevents merge if validation fails

3. **Coverage tracking:**
   - Tracks coverage over time
   - Comments on PRs if coverage decreases

### Required Checks

All of these MUST pass before PR can be merged:

- ✓ validation / validation
- ✓ validation / coverage
- ✓ validation / lint-check

## Best Practices

### For Code Quality

1. **Write tests as you code** (TDD)
   - Tests guide your design
   - Easier to maintain later

2. **Use type hints everywhere**
   - Helps IDE autocomplete
   - Catches errors before runtime

3. **Keep functions small**
   - Easier to test
   - Easier to understand

4. **Run validation frequently**
   - Don't wait until commit
   - Fix issues as you go

### For Performance

1. **Run with --skip-slow during development**
   - Faster feedback loop
   - Full tests before push

2. **Use pytest markers**
   ```bash
   # Skip slow tests
   pytest -m "not slow"
   ```

3. **Cache test results**
   - Pytest does this automatically
   - Use --cache-clear to reset

## Troubleshooting

### "validation.sh: command not found"

```bash
# Make sure you're in project root
cd /path/to/whatsappAItutor

# Run with full path
bash scripts/validate.sh
```

### "pytest: command not found"

```bash
# Install dev dependencies
pip install -e ".[dev]"
```

### "mypy: command not found"

```bash
# Install dev dependencies
pip install -e ".[dev]"
```

### Git hooks not running

```bash
# Reinstall git hooks
bash scripts/install-git-hooks.sh

# Verify they're installed
ls -la .git/hooks/pre-commit
```

### "All checks passed but commit still blocked"

```bash
# Check if there are untracked changes
git status

# Stage everything
git add .

# Try commit again
git commit
```

## Summary

The E2E validation pipeline is a **safety net** that ensures:

✓ Code is consistently formatted
✓ No obvious bugs are committed
✓ Type errors are caught early
✓ Test coverage is maintained
✓ Sensitive files aren't committed
✓ All code works together

By passing this pipeline, you can be confident that:
- The code will work on other machines
- It's safe to push to the main branch
- Others can review it effectively
- It integrates well with the existing codebase
