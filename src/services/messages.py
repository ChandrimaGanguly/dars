"""Centralized bilingual message strings for Telegram bot responses.

PHASE7-A-2 (REQ-021): All student-facing strings not already handled by
EncouragementService or HintGenerator live here. Strings are keyed by
the MessageKey enum and retrieved via get_message().

Strings are stored in code (not the DB) for Phase 0. Migration to
MessageTemplate rows is deferred to Phase 1+ (GAP-3 in PHASE7_TASKS.md).
"""

from __future__ import annotations

from enum import Enum

from src.logging import get_logger

_FALLBACK = "en"
_logger = get_logger(__name__)


class MessageKey(str, Enum):
    """Stable identifiers for bilingual student-facing messages."""

    WELCOME = "welcome"
    HELP = "help"
    SESSION_COMPLETE_SCORE = "session_complete_score"
    NO_ACTIVE_SESSION = "no_active_session"
    ALREADY_COMPLETED = "already_completed"
    UNKNOWN_COMMAND = "unknown_command"
    ERROR_GENERIC = "error_generic"
    LANGUAGE_PROMPT = "language_prompt"
    LANGUAGE_CONFIRMED_EN = "language_confirmed_en"
    LANGUAGE_CONFIRMED_BN = "language_confirmed_bn"
    LANGUAGE_INVALID = "language_invalid"
    REGISTER_FIRST = "register_first"
    NO_PROBLEMS_FOUND = "no_problems_found"
    SESSION_EXPIRED = "session_expired"
    ERROR_PROBLEM_NOT_FOUND = "error_problem_not_found"
    ERROR_STUDENT_NOT_FOUND = "error_student_not_found"
    HINTS_EXHAUSTED = "hints_exhausted"
    # Onboarding flow (multi-step /start)
    ONBOARDING_GRADE_PROMPT = "onboarding_grade_prompt"
    ONBOARDING_INVALID_GRADE = "onboarding_invalid_grade"
    ONBOARDING_COMPLETE = "onboarding_complete"


# Bilingual message templates.  All {placeholders} are documented inline.
MESSAGES: dict[str, dict[str, str]] = {
    # {name} — student's first name
    MessageKey.WELCOME: {
        "en": (
            "Welcome to Dars, {name}! \U0001f393\n\n"
            "I'm your AI tutor. Send /practice to start learning!\n\n"
            "/practice — Daily problems\n"
            "/streak   — Streak calendar\n"
            "/language — Change language"
        ),
        "bn": (
            "Dars-এ স্বাগতম, {name}! \U0001f393\n\n"
            "আমি তোমার AI টিউটর। অনুশীলন শুরু করতে /practice লেখো!\n\n"
            "/practice — প্রতিদিনের প্রশ্ন\n"
            "/streak   — ধারা ক্যালেন্ডার\n"
            "/language — ভাষা পরিবর্তন"
        ),
    },
    MessageKey.HELP: {
        "en": (
            "/practice — Start your daily practice\n"
            "/hint     — Get a hint for the current question\n"
            "/streak   — View your streak calendar\n"
            "/language — Change language (English/বাংলা)\n"
            "/start    — Register as a student"
        ),
        "bn": (
            "/practice — অনুশীলন শুরু করো\n"
            "/hint     — hint পাও\n"
            "/streak   — তোমার ধারা দেখো\n"
            "/language — ভাষা পরিবর্তন করো (English/বাংলা)\n"
            "/start    — নিবন্ধন করো"
        ),
    },
    # {correct} — number correct, {total} — total problems
    MessageKey.SESSION_COMPLETE_SCORE: {
        "en": "Practice complete! You got {correct}/{total} correct. \U0001f3c6 See you tomorrow!",
        "bn": (
            "অনুশীলন শেষ! তুমি {total}টির মধ্যে {correct}টি সঠিক করেছ। " "\U0001f3c6 কাল আবার এসো!"
        ),
    },
    MessageKey.NO_ACTIVE_SESSION: {
        "en": "No active practice session. Type /practice to start.",
        "bn": "কোনো সক্রিয় অনুশীলন নেই। /practice লিখে শুরু করো।",
    },
    MessageKey.ALREADY_COMPLETED: {
        "en": "Today's practice is complete! Come back tomorrow. \U0001f4da",
        "bn": "আজকের অনুশীলন শেষ! কাল আবার এসো। \U0001f4da",
    },
    MessageKey.UNKNOWN_COMMAND: {
        "en": (
            "I don't understand that command.\n\n"
            "/practice — Start your daily practice\n"
            "/hint     — Get a hint for the current question\n"
            "/streak   — View your streak calendar\n"
            "/language — Change language\n"
            "/start    — Register as a student"
        ),
        "bn": (
            "আমি এটা বুঝতে পারছি না।\n\n"
            "/practice — অনুশীলন শুরু করো\n"
            "/hint     — hint পাও\n"
            "/streak   — তোমার ধারা দেখো\n"
            "/language — ভাষা পরিবর্তন করো\n"
            "/start    — নিবন্ধন করো"
        ),
    },
    MessageKey.ERROR_GENERIC: {
        "en": "Something went wrong. Please try again.",
        "bn": "একটি ত্রুটি হয়েছে। আবার চেষ্টা করো।",
    },
    # Language selection prompt — shown in both languages regardless of current language
    MessageKey.LANGUAGE_PROMPT: {
        "en": "Choose your language / আপনার ভাষা বেছে নিন:\n1. English\n2. বাংলা",
        "bn": "Choose your language / আপনার ভাষা বেছে নিন:\n1. English\n2. বাংলা",
    },
    MessageKey.LANGUAGE_CONFIRMED_EN: {
        "en": "Language set to English! All future messages will be in English.",
        "bn": "Language set to English! All future messages will be in English.",
    },
    MessageKey.LANGUAGE_CONFIRMED_BN: {
        "en": "ভাষা বাংলায় সেট হয়েছে! সব ভবিষ্যৎ বার্তা বাংলায় আসবে।",
        "bn": "ভাষা বাংলায় সেট হয়েছে! সব ভবিষ্যৎ বার্তা বাংলায় আসবে।",
    },
    MessageKey.LANGUAGE_INVALID: {
        "en": "Invalid choice. Please reply with 1 (English) or 2 (বাংলা).",
        "bn": "অবৈধ পছন্দ। অনুগ্রহ করে 1 (English) বা 2 (বাংলা) দিয়ে উত্তর দিন।",
    },
    # Shown when student is not registered — bilingual since language unknown
    MessageKey.REGISTER_FIRST: {
        "en": (
            "Please type /start to register.\n"
            "আপনাকে খুঁজে পাওয়া যাচ্ছে না। /start লিখে নিবন্ধন করুন।"
        ),
        "bn": (
            "Please type /start to register.\n"
            "আপনাকে খুঁজে পাওয়া যাচ্ছে না। /start লিখে নিবন্ধন করুন।"
        ),
    },
    MessageKey.NO_PROBLEMS_FOUND: {
        "en": "No problems available for today. Please try again later.",
        "bn": "আজকের জন্য কোনো প্রশ্ন পাওয়া যায়নি। দয়া করে পরে চেষ্টা করুন।",
    },
    MessageKey.SESSION_EXPIRED: {
        "en": "Your practice session has expired. Type /practice to start a new one.",
        "bn": "অনুশীলনের সময় শেষ হয়ে গেছে। /practice লিখে নতুন করে শুরু করো।",
    },
    MessageKey.ERROR_PROBLEM_NOT_FOUND: {
        "en": "Error: Problem not found.",
        "bn": "ত্রুটি: প্রশ্ন খুঁজে পাওয়া যায়নি।",
    },
    MessageKey.ERROR_STUDENT_NOT_FOUND: {
        "en": "Error: Student not found.",
        "bn": "ত্রুটি: শিক্ষার্থীকে খুঁজে পাওয়া যাচ্ছে না।",
    },
    MessageKey.HINTS_EXHAUSTED: {
        "en": "You have used all 3 hints for this problem.",
        "bn": "এই প্রশ্নের জন্য সর্বোচ্চ ৩টি hint ব্যবহার করা হয়ে গেছে।",
    },
    MessageKey.ONBOARDING_GRADE_PROMPT: {
        "en": "Welcome to Dars! \U0001f393 What grade are you in?\n\nReply with:\n6 — Class VI\n7 — Class VII\n8 — Class VIII",
        "bn": "Dars-এ স্বাগতম! \U0001f393 তুমি কোন শ্রেণীতে পড়ো?\n\nউত্তর দাও:\n6 — ষষ্ঠ শ্রেণী\n7 — সপ্তম শ্রেণী\n8 — অষ্টম শ্রেণী",
    },
    MessageKey.ONBOARDING_INVALID_GRADE: {
        "en": "Please reply with 6, 7, or 8 for your grade.",
        "bn": "অনুগ্রহ করে 6, 7, বা 8 দিয়ে তোমার শ্রেণী জানাও।",
    },
    # {name} — student's first name
    MessageKey.ONBOARDING_COMPLETE: {
        "en": (
            "You're all set, {name}! \U0001f389\n\n"
            "Type /practice to start your first session.\n"
            "Type /help to see all commands."
        ),
        "bn": (
            "সব ঠিক হয়ে গেছে, {name}! \U0001f389\n\n"
            "প্রথম অনুশীলন শুরু করতে /practice লেখো।\n"
            "সব command দেখতে /help লেখো।"
        ),
    },
}


def get_message(key: MessageKey, language: str, **kwargs: str | int) -> str:
    """Return the message for key in the requested language.

    Falls back to English if the language is unsupported or the key has
    no entry for that language.

    Args:
        key: MessageKey enum value identifying the message template.
        language: Preferred language code ('en' or 'bn').
        **kwargs: Named substitution values for format placeholders.

    Returns:
        Formatted message string in the requested language.
    """
    lang = language if language in ("en", "bn") else _FALLBACK
    variants = MESSAGES.get(key, {})
    template = variants.get(lang) or variants.get(_FALLBACK) or str(key)
    if not kwargs:
        return template
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        _logger.error(
            "get_message format error — missing placeholder kwarg",
            message_key=str(key),
            language=lang,
            provided_kwargs=list(kwargs.keys()),
        )
        return template  # safe fallback: return unformatted template
