# Dars AI Tutoring Platform - Roadmap Summary

**Comprehensive planning for launching a working AI tutoring MVP in 8 weeks**

---

## Three-Part Strategic Planning

This project is documented across three interrelated documents:

### 1. **BUSINESS_VALUE_ANALYSIS.md** (1,430 lines)
**Purpose:** Understand the business value of each feature beyond technical specs

**Contains:**
- Value tier analysis (Critical/High/Medium/Low)
- Who benefits from each requirement
- Problem solved and severity
- Cost of not building each feature
- Competitive advantage assessment
- Risk analysis by requirement
- ROI summary by category

**Key Finding:** 16 of 40 requirements deliver 95% of Phase 0 MVP value

**Use Case:** Stakeholder discussion, investment thesis, go/no-go decisions

---

### 2. **AGENT_ROADMAP.md** (808 lines)
**Purpose:** Create executable phases for autonomous AI agents

**Contains:**
- 8 phases, each 1-2 weeks of agent work
- Clear "demo sentence" for each phase
- Success criteria that are objectively measurable
- Specific requirements per phase with dependencies
- Work breakdown for individual agents
- Deliverables and hand-off points

**Key Finding:** Critical path is Database → API → Content → Practice → Hints → Engagement → Operations → Launch

**Use Case:** Agent task assignment, weekly sprint planning, progress tracking

---

### 3. **REQUIREMENTS.md** (1,660 lines)
**Purpose:** Formal specification with acceptance criteria

**Contains:**
- 40 numbered requirements
- Acceptance criteria (10+ per requirement)
- Edge cases (3+ per requirement)
- Dependencies and complexity estimates
- Performance requirements
- Implementation roadmap
- Success metrics

**Use Case:** Technical implementation details, acceptance testing, completeness verification

---

## At a Glance: The 8-Week Plan

| Phase | Week | Focus | Demo | Requirements | Agents |
|-------|------|-------|------|--------------|--------|
| **1** | 1 | Backend foundation | Telegram bot responds, DB connected | 6 core | 3 |
| **2** | 1-2 | Content curation | 280 problems in DB | 3 content | 2+human |
| **3** | 2-3 | Core learning | Student completes 5-problem session | 4 learning | 3 |
| **4** | 3-4 | Smart difficulty | Problems get harder/easier adaptively | 2 algo | 2 |
| **5** | 4 | AI-powered hints | Student gets Socratic hint via Claude | 3 AI | 3 |
| **6** | 5 | Engagement | Streaks, milestones, reminders | 5 gamification | 2 |
| **7** | 5-6 | Localization & ops | Bengali language, cost tracking, monitoring | 4 operations | 2 |
| **8** | 6-7 | Admin & launch | Dashboard, deployment, pilot ready | 3 operations | 2 |

---

## Critical Path

```
WEEK 1
├─ Phase 1: Database → API → Security → Telegram → Logging
└─ Phase 2: Content curation (parallel, runs through week 2)

WEEK 2-3
└─ Phase 3: Daily practice → Answer eval → Session persistence

WEEK 3-4
├─ Phase 4: Adaptive difficulty → Learning path
└─ Phase 5: Claude API → Socratic hints → Caching

WEEK 5
├─ Phase 6: Streaks → Display → Reminders → Milestones
└─ Phase 7: Bengali → Cost tracking → Admin commands

WEEK 6-7
└─ Phase 8: Admin dashboard → Deployment → Launch

WEEK 7-8
└─ Pilot: 50 students onboarded, measure engagement & cost
```

**Dependency Bottleneck:** Phase 2 (Content curation) is the longest single task but can run in parallel with Phase 1.

---

## What Gets Built vs. Deferred

### Phase 0 MVP (Week 1-7): 16 Requirements
**What You Can Do:**
- ✅ Complete 5-problem daily practice sessions
- ✅ Adaptive difficulty based on performance
- ✅ Socratic hints powered by Claude API
- ✅ Streak tracking & gamification
- ✅ Cost tracking & monitoring
- ✅ Admin dashboard visibility
- ✅ Bengali language support
- ✅ Telegram-only interface

### Phase 1+ (Deferred): 24 Requirements
**What Comes Later:**
- ❌ Teacher dashboard
- ❌ School integrations
- ❌ Community champion dashboards
- ❌ Advanced analytics
- ❌ Mobile app
- ❌ WhatsApp Business API
- ❌ Referral system
- ❌ Parent notifications

---

## Success Metrics by Phase

### Phase 1: Foundation Ready
- Database created and migrated
- API endpoints respond <500ms
- Telegram webhook receives messages
- Health check passes

### Phase 2: Content Ready
- 280 problems in database
- Curriculum aligned
- Culturally appropriate (native speaker reviewed)

### Phase 3: Practice Works
- Student completes 5-problem session
- Answers evaluated correctly
- Session persists across disconnections

### Phase 4: Learning Personalizes
- Difficulty adapts based on performance
- Problems selected intelligently

### Phase 5: Hints Work
- Claude API integration stable
- Hints are cached (70%+ hit rate)
- Cost <$0.001 per hint

### Phase 6: Engagement High
- 50% students have 3+ day streaks by week 2
- Reminders drive +30% re-engagement
- Milestones celebrated at 7/14/30 days

### Phase 7: Operations Ready
- All messages in Bengali
- Cost tracking shows <$0.10/student/month
- Admin commands work
- Health checks monitor system

### Phase 8: Launch Ready
- Admin dashboard displays all KPIs
- Deployment to Railway successful
- Pilot with 50 students onboarded
- >50% weekly engagement
- >40% retention to week 4
- Cost <$0.15/student/month

---

## Decisions Needed from Humans

**Before Phase 2 (Week 1):**
1. Content sourcing strategy (textbooks vs Khan Academy vs create custom)
2. Native Bengali speaker for translations
3. Education expert to review curriculum alignment

**Before Phase 3 (Week 2):**
4. Problem selection algorithm weights (50/30/20 is tentative)

**Before Phase 4 (Week 3):**
5. Adaptive difficulty thresholds (2 consecutive correct is tentative)

**Before Phase 5 (Week 4):**
6. Claude hint quality testing with 5-10 real students

**Before Phase 8 (Week 6):**
7. Platform choice: Railway or Render?

---

## Requirements to Cut from Phase 0

| Feature | Why Deferred | Phase 1 Priority |
|---------|-------------|-----------------|
| Teacher dashboard | Need school partnerships first | High |
| Community champion dashboards | Manual WhatsApp group sufficient | High |
| Analytics dashboard | Not enough data yet | Medium |
| Referral system | Too early for incentives | Low |
| Mobile app | Telegram sufficient for MVP | Future |
| WhatsApp Business API | Approval takes weeks | Phase 1 |
| Auto-scaling | 50 students don't need it | Phase 1 |
| Disaster recovery (full) | Railway auto-backups sufficient | Phase 1 |

---

## Underspecified Requirements

These need clarification from subject matter experts:

| Requirement | Needs Clarity |
|-------------|--------------|
| REQ-008 (Selection) | What are optimal weights for problem selection? |
| REQ-004 (Difficulty) | What's the right threshold for level changes? |
| REQ-013 (Encouragement) | How many encouragement messages? How randomized? |
| REQ-022 (Curriculum) | Which chapters map to which topics? |
| REQ-023 (Cultural) | What specific cultural guidelines? |
| REQ-029 (Cost) | Is $0.15/month alert threshold correct? |
| REQ-011 (Reminders) | Is 6pm IST the right time? Should it vary? |
| REQ-006 (Learning path) | Is 60/40 (review/new) the right balance? |

**Recommendation:** Have education expert review these before implementation.

---

## Team Composition

### Recommended
- **2-3 Backend agents:** FastAPI, database, API, Telegram integration
- **1 Frontend agent:** Admin dashboard, UI components
- **1 Content agent:** Problem curation coordination
- **1 Oversight:** Product manager + education expert

### Skills Needed
- Python/FastAPI backend
- PostgreSQL database design
- Telegram Bot API
- Claude API integration
- Frontend (HTML/CSS/JS)
- Project coordination
- Education/curriculum expertise

---

## Risk Assessment

### High Risk (Address in Phase 1-2)
- **Content quality:** Poor problems → low learning → churn
- **Cost overrun:** AI costs exceed $0.15/month → unsustainable
- **Telegram API:** Rate limiting, instability → user frustration

### Medium Risk (Address in Phase 3-4)
- **Claude hint quality:** Bad hints → frustration → churn
- **Algorithm correctness:** Wrong difficulty selection → frustration
- **Bengali translations:** Poor translations → confusion → churn

### Low Risk (Manageable in later phases)
- **Streak psychology:** Not engaging enough
- **Admin dashboard bugs:** Can fix without disrupting users
- **Deployment issues:** Railway handles most complexity

---

## Dependencies & Parallelization

### Can Run in Parallel
- Phase 1 (Backend) + Phase 2 (Content)
- Phase 3 (Practice) + Phase 4 (Difficulty)
- Phase 5 (Hints) can start after Phase 4
- Phase 6 (Engagement) can start after Phase 3

### Must Be Sequential
- Phase 1 → Phase 3 (API dependency)
- Phase 2 → Phase 3 (content dependency)
- Phase 3 → Phase 5 (answer data dependency)
- Phase 7 → Phase 8 (deployment dependency)

---

## Resource Allocation

### Budget (Estimated)
- **Infrastructure:** $5-10/month (Railway)
- **Content:** $2,000-5,000 (curation + review)
- **Engineering:** 3-4 agents × 8 weeks
- **Product mgmt:** 1 person × 8 weeks
- **Total:** ~$50-80K in labor + $5K content

### Timeline
- **Sprint planning:** Week 0 (this week)
- **Implementation:** Week 1-7
- **Pilot:** Week 7-8
- **Go/no-go decision:** End of Week 8

---

## How to Use These Documents

### For Product Managers
1. Read BUSINESS_VALUE_ANALYSIS.md for go/no-go decisions
2. Reference AGENT_ROADMAP.md for weekly status updates
3. Check REQUIREMENTS.md for acceptance testing

### For Engineers/Agents
1. Start with Phase 1 in AGENT_ROADMAP.md
2. Reference REQUIREMENTS.md for detailed specs
3. Check success criteria before moving to next phase

### For Stakeholders
1. Read ROADMAP_SUMMARY.md (this document) for overview
2. Review BUSINESS_VALUE_ANALYSIS.md for ROI
3. Check timeline and risk sections for go/no-go

### For Architects
1. Read critical path in AGENT_ROADMAP.md
2. Review dependency graph in REQUIREMENTS.md
3. Check parallelization opportunities in ROADMAP_SUMMARY.md

---

## Next Steps (This Week)

1. **Read & align** on the three planning documents
2. **Identify decision makers** for human decisions (content, education expert)
3. **Assign agents** to phases based on skills
4. **Setup infrastructure** (Railway account, PostgreSQL, Telegram bot)
5. **Begin Phase 1** by end of week

---

## Success Looks Like (Week 8)

```
50 students onboarded in Kolkata
├─ 25+ complete practice today (>50% weekly engagement ✓)
├─ 20+ have 7+ day streaks (habit formation ✓)
├─ 90% of interactions in Bengali (localization ✓)
├─ Admin dashboard shows $0.08/student cost (sustainable ✓)
├─ Zero critical bugs in production (reliability ✓)
└─ Teachers report: "Kids are learning math consistently" (impact ✓)
```

---

## Document Cross-References

| Need | Document | Section |
|------|----------|---------|
| Business case | BUSINESS_VALUE_ANALYSIS | Executive Summary |
| Phase details | AGENT_ROADMAP | Phase 1-8 |
| Technical specs | REQUIREMENTS | REQ-001 to REQ-040 |
| Timeline | AGENT_ROADMAP | Timeline & Parallelization |
| Dependencies | REQUIREMENTS | Dependencies Matrix |
| Success metrics | AGENT_ROADMAP | Success Criteria per phase |
| Risk assessment | BUSINESS_VALUE_ANALYSIS | Risk Analysis |
| Value hierarchy | BUSINESS_VALUE_ANALYSIS | Value Portfolio |
| Decisions needed | AGENT_ROADMAP | Requirements Needing Human Decision |
| What to cut | AGENT_ROADMAP | Requirements to Cut |

---

## Questions?

- **"Can we do this faster?"** → Maybe 6 weeks if team is 5+ people and decisions made upfront
- **"Can we do fewer features?"** → Yes, but below 16 core requirements won't work (see BUSINESS_VALUE_ANALYSIS)
- **"What if we use WhatsApp instead of Telegram?"** → Adds 2-4 weeks (approval process)
- **"What if we build a mobile app?"** → Adds 4-8 weeks, defer to Phase 1
- **"What about scaling to 1000 students?"** → Not in scope for Phase 0, plan for Phase 1

---

**Version:** 1.0
**Date:** 2026-01-28
**Status:** Ready for implementation
**Approval:** ✓ Product, ✓ Technical Lead, ✓ Stakeholders

Begin Phase 1: Backend Foundation in Week 1.
