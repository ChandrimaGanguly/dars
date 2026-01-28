# Frontend Tasks

> Telegram bot interface, message formatting, user interactions
> (Future: Teacher web dashboard)

## Active

### Phase 1: Foundation

- [ ] TASK-003: Create Telegram bot via BotFather
  - **Status:** ready
  - **Notes:** Register bot, get token, set commands (/start, /practice, /streak, /help)

- [ ] TASK-004: Implement basic Telegram webhook handler
  - **Status:** ready
  - **Blocked by:** TASK-001, TASK-003
  - **Notes:** FastAPI route /webhook, parse messages, return 200 OK

### Phase 2: User Interface

- [ ] TASK-F01: Design conversation flow diagrams
  - **Status:** ready
  - **Notes:** Map out all user journeys: onboarding, practice, hints, streak check

- [ ] TASK-F02: Create inline keyboard layouts
  - **Status:** ready
  - **Blocked by:** TASK-004
  - **Notes:** Grade selection, language selection, hint request, answer choices

- [ ] TASK-F03: Design message templates (Bengali)
  - **Status:** ready
  - **Notes:** All user-facing messages in Bengali with emoji

- [ ] TASK-F04: Design message templates (English)
  - **Status:** ready
  - **Notes:** English versions for bilingual support

### Phase 9: Testing

- [ ] TASK-040: End-to-end testing with test accounts
  - **Status:** ready
  - **Blocked by:** All Phase 1-6 tasks
  - **Notes:** 3 test accounts, full flows, edge cases

- [ ] TASK-041: Bengali language QA
  - **Status:** ready
  - **Blocked by:** TASK-F03
  - **Notes:** Native speaker review of all Bengali text

---

## Future (Phase 1+)

### Teacher Dashboard (Web)

- [ ] TASK-F10: Design teacher dashboard wireframes
  - **Status:** not_started
  - **Notes:** Class view, student progress, struggling students

- [ ] TASK-F11: Implement basic dashboard with FastAPI templates
  - **Status:** not_started
  - **Notes:** Simple HTML/Jinja2, no React needed for MVP

---

## Completed

_None yet_
