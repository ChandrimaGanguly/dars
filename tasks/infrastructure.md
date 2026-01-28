# Infrastructure Tasks

> Deployment, monitoring, DevOps, CI/CD

## Active

### Phase 7: Deployment

- [ ] TASK-028: Set up Railway/Render deployment
  - **Status:** ready
  - **Notes:** Create project, configure build, set env vars, PostgreSQL add-on

- [ ] TASK-029: Configure Telegram webhook for production
  - **Status:** ready
  - **Blocked by:** TASK-028
  - **Notes:** Set webhook URL, verify receiving messages

- [ ] TASK-030: Implement health check endpoint
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** /health returns 200, checks DB and Claude API

- [ ] TASK-031: Add logging and error tracking
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** Structured JSON logging, consider Sentry free tier

- [ ] TASK-032: Implement cost tracking dashboard
  - **Status:** ready
  - **Blocked by:** TASK-014
  - **Notes:** Track Claude API calls per student, daily/weekly/monthly costs

### Phase 9: Testing & Operations

- [ ] TASK-T01: Set up pytest for unit tests
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** Configure pytest, create tests/ directory, fixtures for DB and API

- [ ] TASK-T02: Write unit tests (core logic)
  - **Status:** ready
  - **Blocked by:** TASK-T01
  - **Notes:** Streak calculation, problem selection, answer evaluation. Target: >80% coverage on core modules

- [ ] TASK-T03: Write integration tests
  - **Status:** ready
  - **Blocked by:** TASK-020
  - **Notes:** Full practice flow, Telegram message handling, DB persistence

- [ ] TASK-T04: Set up linting with ruff/black
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** Code style enforcement, auto-formatting

- [ ] TASK-T05: Set up type checking with mypy
  - **Status:** ready
  - **Blocked by:** TASK-001
  - **Notes:** Static type analysis, catch type errors

- [ ] TASK-T06: Configure pre-commit hooks
  - **Status:** ready
  - **Blocked by:** TASK-T04, TASK-T05
  - **Notes:** Hook config for unit tests, integration tests, lint, typecheck before commit

- [ ] TASK-042: Load testing
  - **Status:** ready
  - **Blocked by:** TASK-028
  - **Notes:** Simulate 50 concurrent students, verify <2s response

- [ ] TASK-043: Create runbook for common issues
  - **Status:** ready
  - **Notes:** Bot not responding, DB issues, Claude errors, restart procedures

### Validation Pipeline (DONE ✓)

- [x] TASK-E01: Create E2E validation pipeline script (completed 2026-01-28)
  - **Status:** complete
  - **Notes:** scripts/validate.sh - 7-stage pipeline with --fix and --verbose options

- [x] TASK-E02: Create git pre-commit hook for validation (completed 2026-01-28)
  - **Status:** complete
  - **Notes:** scripts/git-hook-pre-commit.sh - Prevents commits if validation fails

- [x] TASK-E03: Create git hook installation script (completed 2026-01-28)
  - **Status:** complete
  - **Notes:** scripts/install-git-hooks.sh - One-command setup

- [x] TASK-E04: Create GitHub Actions workflow for CI/CD (completed 2026-01-28)
  - **Status:** complete
  - **Notes:** .github/workflows/validation.yml - Runs on every push/PR

- [x] TASK-E05: Create validation pipeline documentation (completed 2026-01-28)
  - **Status:** complete
  - **Notes:** VALIDATION_PIPELINE.md - 400+ lines, comprehensive guide

- [x] TASK-E06: Create agent development checklist (completed 2026-01-28)
  - **Status:** complete
  - **Notes:** AGENT_CHECKLIST.md - Step-by-step for autonomous agents

### Environment Setup

- [ ] TASK-I01: Create .env.example with all required variables
  - **Status:** ready
  - **Notes:** TELEGRAM_BOT_TOKEN, DATABASE_URL, ANTHROPIC_API_KEY, etc.

- [ ] TASK-I02: Set up development environment documentation
  - **Status:** ready
  - **Notes:** README with setup instructions, Docker compose for local Postgres

- [ ] TASK-I03: Configure GitHub repository
  - **Status:** ready
  - **Notes:** .gitignore, branch protection, PR template

### CI/CD (Future)

- [ ] TASK-I10: Set up GitHub Actions for tests
  - **Status:** not_started
  - **Notes:** Run pytest on PR

- [ ] TASK-I11: Set up auto-deploy on main branch
  - **Status:** not_started
  - **Notes:** Railway/Render auto-deploy from GitHub

---

## Completed

_None yet_
