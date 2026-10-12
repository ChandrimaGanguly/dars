# Bilingual Content Coverage (REQ-021)

**Status**: ✅ Complete database schema support for all bilingual content

This document tracks bilingual (Bengali + English) content support across the Dars platform.

## 📊 Coverage Summary

| Content Type | Model/Table | Status | Fields |
|--------------|-------------|--------|--------|
| **Problem Statements** | `problems` | ✅ Complete | `question_en`, `question_bn` |
| **Hints** | `problems.hints` (JSON) | ✅ Complete | `text_en`, `text_bn` per hint |
| **Feedback Messages** | `message_templates` | ✅ Complete | `message_en`, `message_bn` |
| **Milestone Messages** | `message_templates` | ✅ Complete | `message_en`, `message_bn` |
| **Notifications** | `message_templates` | ✅ Complete | `message_en`, `message_bn` |
| **UI Text** | `message_templates` | ✅ Complete | `message_en`, `message_bn` |
| **Error Messages** | `message_templates` | ✅ Complete | `message_en`, `message_bn` |
| **Student Preferences** | `students` | ✅ Complete | `language` (en/bn) |

---

## 🗃️ Database Models

### 1. Problem Model (`problems` table)

**Bilingual Fields:**
- `question_en` (Text) - Problem statement in English
- `question_bn` (Text) - Problem statement in Bengali
- `hints` (JSON) - Array of hint objects with `text_en` and `text_bn`

**Example:**
```python
problem = Problem(
    question_en="A shopkeeper buys 15 mangoes for Rs. 300...",
    question_bn="একজন দোকানদার 15টি আম ₹300 এর জন্য ক্রয় করেন...",
    hints=[
        {
            "hint_number": 1,
            "text_en": "Think about the cost of each item first.",
            "text_bn": "প্রথমে প্রতিটি জিনিসের খরচ সম্পর্কে চিন্তা করুন।",
            "is_ai_generated": False
        }
    ]
)
```

### 2. MessageTemplate Model (`message_templates` table) - NEW

**Purpose**: Centralized storage for all user-facing messages with variable interpolation.

**Bilingual Fields:**
- `message_en` (Text) - English message template with `{variable}` placeholders
- `message_bn` (Text) - Bengali message template with `{variable}` placeholders

**Categories:**
- `feedback` - Answer evaluation responses
- `milestone` - Streak achievement messages
- `notification` - Reminders and encouragement
- `ui` - Buttons, labels, common UI text
- `error` - Validation and system errors

**Example:**
```python
# Retrieve and format message
template = await db.get(MessageTemplate, "streak_milestone_7")
message = template.get_message("bn", student_name="রহিম")
# Returns: "রহিম, অভিনন্দন! আপনি ৭ দিনের ধারাবাহিকতা অর্জন করেছেন! 🔥"
```

**Seed Data** (11 messages included in migration):

| Message Key | Category | English | Bengali |
|-------------|----------|---------|---------|
| `feedback_correct` | feedback | "Correct! Well done! 🎉" | "সঠিক! সাবাশ! 🎉" |
| `feedback_incorrect` | feedback | "Not quite right. Try again..." | "ঠিক নয়। আবার চেষ্টা করুন..." |
| `feedback_correct_with_hints` | feedback | "Correct! You used {hints_used} hint(s)..." | "সঠিক! আপনি {hints_used}টি ইঙ্গিত..." |
| `milestone_7day` | milestone | "Amazing! 7 day streak! 🔥" | "অসাধারণ! ৭ দিনের ধারাবাহিকতা! 🔥" |
| `milestone_14day` | milestone | "Incredible! 14 days in a row! 💪" | "অবিশ্বাস্য! পরপর ১৪ দিন! 💪" |
| `milestone_30day` | milestone | "Spectacular! 30 day streak! 🌟" | "দুর্দান্ত! ৩০ দিনের ধারাবাহিকতা! 🌟" |
| `reminder_practice` | notification | "Don't forget to practice today!..." | "আজ অনুশীলন করতে ভুলবেন না!..." |
| `encouragement_start` | notification | "Let's start your practice! 💫" | "চলুন আপনার অনুশীলন শুরু করি! 💫" |
| `ui_next_problem` | ui | "Next Problem" | "পরবর্তী সমস্যা" |
| `ui_submit_answer` | ui | "Submit Answer" | "উত্তর জমা দিন" |
| `ui_request_hint` | ui | "Request Hint" | "ইঙ্গিত চান" |

### 3. Student Model (`students` table)

**Bilingual Field:**
- `language` (String) - User's preferred language (`en` or `bn`, default: `bn`)

---

## 📝 Migration

**Migration File**: `alembic/versions/4822235d35e4_add_message_templates_for_bilingual_.py`

**Changes:**
1. Creates `message_templates` table with all bilingual fields
2. Adds indexes on `category` and `message_key` for efficient lookups
3. Adds check constraint for valid category values
4. Adds unique constraint on `message_key`
5. Seeds 11 common messages for immediate use

**Run Migration:**
```bash
alembic upgrade head
```

**Rollback Migration:**
```bash
alembic downgrade -1
```

---

## 🔧 Usage Examples

### Retrieving Messages in Service Layer

```python
from sqlalchemy import select
from src.models import MessageTemplate

# Get feedback message
async def get_feedback_message(
    db: AsyncSession,
    is_correct: bool,
    hints_used: int,
    language: str
) -> str:
    """Get appropriate feedback message based on answer correctness."""
    if is_correct:
        if hints_used > 0:
            key = "feedback_correct_with_hints"
        else:
            key = "feedback_correct"
    else:
        key = "feedback_incorrect"

    result = await db.execute(
        select(MessageTemplate).where(MessageTemplate.message_key == key)
    )
    template = result.scalar_one()

    if hints_used > 0:
        return template.get_message(language, hints_used=hints_used)
    else:
        return template.get_message(language)
```

### Adding New Messages

```python
# Add new milestone message
new_message = MessageTemplate(
    message_key="milestone_60day",
    category=MessageCategory.MILESTONE,
    message_en="Outstanding! 60 days of dedication! 🏆",
    message_bn="অসাধারণ! ৬০ দিনের নিষ্ঠা! 🏆",
    variables=[],
    description="60 day streak achievement"
)
db.add(new_message)
await db.commit()
```

---

## ✅ Verification Checklist

- [x] **Problem statements** support Bengali and English
- [x] **Hints** support Bengali and English (3 hints per problem)
- [x] **Feedback messages** can be stored and retrieved bilingually
- [x] **Milestone messages** can be stored and retrieved bilingually
- [x] **Notifications** can be stored and retrieved bilingually
- [x] **UI text** can be stored and retrieved bilingually
- [x] **Error messages** can be stored and retrieved bilingually
- [x] **Student language preference** is stored in database
- [x] **Variable interpolation** works for dynamic content (e.g., `{student_name}`, `{days}`)
- [x] **Migration** is reversible (has downgrade function)
- [x] **Seed data** includes 11 common messages
- [x] **Indexes** optimize message lookups

---

## 🎯 Next Steps (Phase 1+)

1. **Create LocalizationService** - Service layer to manage message retrieval
2. **Add More Messages** - Expand seed data with more common messages
3. **Admin Interface** - Allow admins to edit messages without code changes
4. **Message Caching** - Cache frequently used messages in Redis
5. **A/B Testing** - Track which message variants perform better
6. **Regional Dialects** - Support West Bengal vs Bangladesh Bengali variations
7. **Audio Messages** - Add `audio_url_en` and `audio_url_bn` for pronunciation

---

## 📊 REQ-021 Compliance

✅ **All user-facing strings available in Bengali (bn) and English (en)**
- Problem statements: ✅
- Hints: ✅
- Feedback: ✅
- Milestones: ✅
- Notifications: ✅
- UI text: ✅
- Error messages: ✅

✅ **Language selected at /start (default: Bengali)**
- Student.language field supports this (default: 'bn')

✅ **Currency shown as ₹ (Indian Rupee)**
- Problems use ₹ symbol in Bengali content

✅ **RTL support not needed (Bengali is LTR)**
- No special handling required

---

**Status**: ✅ **Complete** - All bilingual content can be recorded in the database.

**Last Updated**: 2026-02-24
**Responsible**: Maryam (Database Expert)
