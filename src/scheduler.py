"""Background scheduler for Dars — daily reminder job.

PHASE6-A-1 / PHASE6-A-2

Uses APScheduler 3.x AsyncIOScheduler. Registered as a FastAPI lifespan
task in src/main.py.

The scheduler fires send_daily_reminders() every day at 12:30 UTC (18:00 IST),
which sends Telegram reminders to students who have not yet practiced today.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from src.database import get_session_factory
from src.logging import get_logger
from src.models.sent_message import SentMessage
from src.models.streak import Streak
from src.models.student import Student
from src.repositories.streak_repository import StreakRepository
from src.services.telegram_client import TelegramClient
from src.utils.pii import hash_telegram_id

logger = get_logger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


async def send_daily_reminders() -> None:
    """Send Telegram reminders to students who have not practiced today.

    REQ-011 rules:
    - Run once per day at 12:30 UTC (18:00 IST) via APScheduler cron job
    - Send only if student has NOT completed practice today (UTC date)
    - streak=0 → motivational message (not "at risk")
    - streak>=1 → "Your N-day streak is at risk" message
    - Uses student.language for bilingual messages
    - Send failures logged as ERROR; processing continues for remaining students
    """
    logger.info("send_daily_reminders: job started")

    factory = get_session_factory()
    today = datetime.now(UTC).date()  # Fix 1: explicit UTC — avoids wrong date on non-UTC servers
    cutoff = today - timedelta(days=30)

    sent_count = 0
    skipped_count = 0
    error_count = 0

    async with factory() as db:
        # Query students who have practiced at least once in the last 30 days
        result = await db.execute(
            select(Student)
            .join(Streak, Streak.student_id == Student.student_id)
            .where(Streak.last_practice_date >= cutoff)
        )
        students = result.scalars().all()

        streak_repo = StreakRepository()
        telegram = TelegramClient()

        # TODO(Phase7): replace per-student queries with a single JOIN + eager-load
        # to avoid 3 DB round-trips per student when scaling beyond the 50-student pilot.
        for student in students:
            hashed_tid = hash_telegram_id(student.telegram_id)  # Fix 2: never log raw telegram_id
            streak_obj = await streak_repo.get_for_student(db, student.student_id)

            # Skip if already practiced today
            if streak_obj is not None:
                raw = streak_obj.last_practice_date
                last_date: date | None = raw.date() if isinstance(raw, datetime) else raw
                if last_date == today:
                    skipped_count += 1
                    logger.info(
                        "reminder_skipped",
                        hashed_telegram_id=hashed_tid,
                        reason="practiced_today",
                    )
                    continue

            # Fix 4: guard against double-fire on app restart within the same UTC day
            reminder_key = f"reminder_{today.isoformat()}"
            already_reminded = (
                await db.execute(
                    select(SentMessage).where(
                        SentMessage.student_id == student.student_id,
                        SentMessage.message_key == reminder_key,
                    )
                )
            ).scalar_one_or_none()
            if already_reminded is not None:
                skipped_count += 1
                logger.info(
                    "reminder_skipped",
                    hashed_telegram_id=hashed_tid,
                    reason="already_reminded_today",
                )
                continue

            current_streak = streak_obj.current_streak if streak_obj is not None else 0

            # Build bilingual reminder message
            if student.language == "bn":
                if current_streak == 0:
                    msg = "\U0001f4da আজকের অনুশীলন সম্পন্ন করো এবং তোমার প্রথম ধারা শুরু করো!"
                else:
                    msg = (
                        f"\u09a4\u09cb\u09ae\u09be\u09b0 {current_streak} \u09a6\u09bf\u09a8\u09c7\u09b0 "
                        f"\u09a7\u09be\u09b0\u09be \u099d\u09c1\u0981\u0995\u09bf\u09a4\u09c7 \u0986\u099b\u09c7! "
                        f"\u0986\u099c\u0995\u09c7\u09b0 \u0985\u09a8\u09c1\u09b6\u09c0\u09b2\u09a8 \u09b8\u09ae\u09cd\u09aa\u09a8\u09cd\u09a8 \u0995\u09b0\u09cb\u0964 \U0001f525"
                    )
            else:
                if current_streak == 0:
                    msg = "\U0001f4da Ready to start your first streak? Complete today's practice!"
                else:
                    msg = (
                        f"Your {current_streak}-day streak is at risk! "
                        f"Complete today's practice to keep it alive. \U0001f525"
                    )

            # Fix 8: narrow try/except to just the network call — programming errors surface
            try:
                await telegram.send_message(student.telegram_id, msg)
            except Exception as exc:
                error_count += 1
                logger.error(
                    "reminder_send_failed",
                    hashed_telegram_id=hashed_tid,
                    error=type(exc).__name__,
                )
                continue

            # Record this reminder so restarts don't double-fire (Fix 4)
            db.add(SentMessage(student_id=student.student_id, message_key=reminder_key))
            await db.commit()  # commit per-student for durability across restarts
            sent_count += 1
            logger.info(
                "reminder_sent",
                hashed_telegram_id=hashed_tid,
                current_streak=current_streak,
            )

    logger.info(
        "send_daily_reminders: job complete",
        sent=sent_count,
        skipped=skipped_count,
        errors=error_count,
    )


def start_scheduler() -> None:
    """Register all background jobs and start the scheduler.

    Adds the daily reminder cron job (12:30 UTC = 18:00 IST) and starts
    the APScheduler event loop integration.
    """
    scheduler.add_job(
        send_daily_reminders,
        trigger="cron",
        hour=12,
        minute=30,  # 12:30 UTC = 18:00 IST
        id="daily_reminders",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info("Scheduler started — daily_reminders job registered at 12:30 UTC")


def stop_scheduler() -> None:
    """Shutdown the scheduler gracefully on app teardown."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
