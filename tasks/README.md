# Task Coordination System

A simple file-based system for tracking and coordinating tasks across the Dars project.

## Directory Structure

```
tasks/
├── README.md           # This file
├── backend.md          # FastAPI, database, Claude API tasks
├── frontend.md         # Telegram bot UI, message formatting (future: web dashboard)
├── infrastructure.md   # Deployment, monitoring, DevOps
├── content.md          # Math problems, translations, curriculum
└── scripts/
    └── task-utils.sh   # Helper scripts for task management
```

## Task File Format

Each task file uses a consistent markdown format:

```markdown
## [AREA] Tasks

### Active
- [ ] TASK-XXX: Brief description
  - **Status:** in_progress | blocked | ready
  - **Assignee:** @name (optional)
  - **Blocked by:** TASK-YYY (if blocked)
  - **Notes:** Additional context

### Completed
- [x] TASK-XXX: Brief description (completed YYYY-MM-DD)
```

## Status Definitions

| Status | Meaning |
|--------|---------|
| `ready` | Can be started, no blockers |
| `in_progress` | Currently being worked on |
| `blocked` | Waiting on another task or external dependency |
| `review` | Implementation done, needs review |
| `done` | Completed and verified |

## Quick Commands

```bash
# View all pending tasks
./tasks/scripts/task-utils.sh pending

# View tasks by area
./tasks/scripts/task-utils.sh area backend

# Add a new task
./tasks/scripts/task-utils.sh add backend "TASK-044" "Implement rate limiting"

# Mark task complete
./tasks/scripts/task-utils.sh complete backend "TASK-001"

# Show task summary
./tasks/scripts/task-utils.sh summary
```

## Manual Task Addition

To add a task manually, edit the appropriate file and add under `### Active`:

```markdown
- [ ] TASK-XXX: Your task description
  - **Status:** ready
  - **Notes:** Any relevant context
```

## Coordination Rules

1. **One owner per task** - If you start a task, add your name as assignee
2. **Update status** - Move tasks between sections as they progress
3. **Note blockers** - If blocked, specify what you're waiting on
4. **Date completions** - Add date when marking done

## Syncing with OpenSpec

The master task list lives in `openspec/changes/dars/tasks.md`. This `tasks/` directory is for day-to-day coordination and can diverge during active development. Sync back to OpenSpec when:
- A phase is complete
- Major scope changes occur
- Before archiving the change
