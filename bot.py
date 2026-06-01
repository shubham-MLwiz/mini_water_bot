"""
Water Reminder Bot — Step 15 (Final)
Added /help command, proper logging, and error handling.
Bot is now feature-complete.
"""

import logging
import os
import re
from datetime import datetime, time as dt_time, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler

from database import init_db, log_water, get_today_total, get_today_logs

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
DAILY_TARGET_ML = int(os.getenv("DAILY_TARGET_ML", "2500"))
WAKE_HOUR = int(os.getenv("WAKE_HOUR", "7"))
SLEEP_HOUR = int(os.getenv("SLEEP_HOUR", "23"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
TZ = ZoneInfo(TIMEZONE)  # Timezone object used by scheduler and pace calculation

# ──────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ──────────────────────────────────────────────────────────────────────
# Python's `logging` module is the standard way to record what your program
# is doing. It's better than print() because:
#   - Messages are timestamped automatically
#   - You can set severity levels (DEBUG, INFO, WARNING, ERROR)
#   - Output goes to both terminal AND a file simultaneously
#   - Libraries (like python-telegram-bot) also use logging, so you see
#     their messages too when debugging
#
# Levels (from least to most severe):
#   DEBUG   → Detailed diagnostic info (usually off in production)
#   INFO    → Confirmation that things are working as expected
#   WARNING → Something unexpected but not broken
#   ERROR   → Something failed
# ──────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),                    # Print to terminal
        logging.FileHandler("bot.log", mode="a"),   # Append to bot.log file
    ]
)
logger = logging.getLogger(__name__)

# Silence the noisy HTTP request logs from httpx and telegram libraries.
# Without these lines, every single poll request (every 3-5 sec) gets logged.
# We only want to see WARNING or ERROR from these — not routine "200 OK" spam.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)

# Reminders are confirmed working. Keep APScheduler at WARNING to reduce noise.
logging.getLogger("apscheduler").setLevel(logging.WARNING)


def authorized_only(func):
    """Decorator that blocks anyone who isn't you.

    How it works:
    - Every Telegram message has a sender (update.effective_user.id)
    - We compare that to YOUR chat ID from .env
    - If it doesn't match, we silently ignore the message
    - If it matches, we run the actual handler function
    """
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CHAT_ID:
            logger.warning(f"Unauthorized user {update.effective_user.id} tried: {update.message.text}")
            return
        return await func(update, context)
    wrapper = wraps(func)(wrapper)
    return wrapper


@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command. Sends a welcome message."""
    logger.info(f"/start from {update.effective_user.first_name}")
    await update.message.reply_text(
        "Hey! I'm your Water Reminder Bot 💧\n\n"
        "I'll remind you to drink water every hour and track your intake.\n\n"
        "Try sending: drank 200 ml\n"
        "Or type /help for all commands."
    )


@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command. Lists all available commands and input formats."""
    logger.info("/help requested")
    await update.message.reply_text(
        "💧 Water Reminder Bot — Help\n"
        "\n"
        "Commands:\n"
        "  /start   — Welcome message\n"
        "  /summary — Today's intake breakdown\n"
        "  /help    — This help text\n"
        "\n"
        "Log water (just type normally):\n"
        "  \"drank 200 ml\"\n"
        "  \"250ml\"\n"
        "  \"200\"\n"
        "  \"just had 300 ml\"\n"
        "\n"
        "Check status (natural language):\n"
        "  \"how much today\"\n"
        "  \"am I lagging behind\"\n"
        "  \"total\" / \"status\" / \"progress\"\n"
        "\n"
        f"🎯 Daily target: {DAILY_TARGET_ML} ml\n"
        f"⏰ Reminders: {WAKE_HOUR}:00 to {SLEEP_HOUR - 1}:00"
    )


@authorized_only
async def test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /testreminder — manually triggers one reminder NOW for debugging.
    
    This calls the exact same send_reminder function that the scheduler calls.
    If this works but scheduled ones don't, the issue is with scheduling.
    If this also fails, the issue is inside send_reminder itself.
    """
    logger.info("/testreminder triggered manually")
    await send_reminder(context)
    await update.message.reply_text("(Test reminder sent — check if you got it above)")


@authorized_only
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /summary command. Shows today's intake breakdown."""
    logger.info("/summary requested")
    await update.message.reply_text(build_summary_text())


def build_summary_text() -> str:
    """Build the summary message text. Used by /summary and natural queries."""
    logs = get_today_logs()
    total = get_today_total()
    remaining = max(0, DAILY_TARGET_ML - total)

    if not logs:
        return (
            "📊 Today's Summary\n"
            "\nNo water logged yet today.\n"
            f"\n🎯 Target: {DAILY_TARGET_ML} ml"
        )

    # Build the log list
    lines = ["📊 Today's Summary\n"]
    for time_str, amount in logs:
        lines.append(f"  {time_str} — {amount} ml")

    lines.append(f"\n📊 Total: {total} ml / {DAILY_TARGET_ML} ml")

    if remaining > 0:
        lines.append(f"🚩 Remaining: {remaining} ml")
    else:
        lines.append("✅ Target reached! Great job!")

    # Add pace comparison
    pace_text = get_pace_text(total)
    if pace_text:
        lines.append(f"\n{pace_text}")

    return "\n".join(lines)


def get_pace_text(total: int) -> str:
    """Compare actual intake vs expected pace for this time of day.

    Logic:
    - You have (SLEEP_HOUR - WAKE_HOUR) waking hours to drink DAILY_TARGET_ML.
    - Expected by now = (hours elapsed since wake) / (total waking hours) * target.
    - If actual < expected → you're behind. If actual >= expected → you're on track.

    Example (target=2500, wake=7, sleep=23, current time=15:00):
    - Waking hours = 16
    - Hours elapsed since 7:00 = 8
    - Expected by now = (8/16) * 2500 = 1250 ml
    - If you've only had 600 ml → "You're 650 ml behind pace"
    """
    now = datetime.now(tz=TZ)  # Use configured timezone, not system local time
    current_hour = now.hour

    # Outside waking hours? No pace info.
    if current_hour < WAKE_HOUR or current_hour >= SLEEP_HOUR:
        return ""

    waking_hours = SLEEP_HOUR - WAKE_HOUR  # e.g. 16
    hours_elapsed = current_hour - WAKE_HOUR  # e.g. 8 at 15:00

    # Avoid division weirdness at the very start of the day
    if hours_elapsed == 0:
        return "🏁 Day just started — keep sipping!"

    expected = int((hours_elapsed / waking_hours) * DAILY_TARGET_ML)
    diff = total - expected

    if diff >= 0:
        return f"✅ On pace! You're {diff} ml ahead of schedule."
    else:
        return f"⚠️ You're {abs(diff)} ml behind pace. Time to catch up!"


# --------------- Custom On-Demand Reminders (Phase 6) --------------- #

def parse_custom_reminder(text: str):
    """Parse custom reminder requests from natural text.

    Returns (delay_seconds, description) if the text is a reminder request,
    or None if it isn't.

    Supported patterns:
      - "remind me in 10 mins"
      - "remind me in 1 hour"
      - "remind in 30 minutes"
      - "remind me in 1.5 hours"
      - "remind again in 20 min"
      - "snooze 15 mins"
      - "snooze for 10 minutes"
      - "remind me at 3:15 pm"
      - "remind at 14:30"
      - "remind me at 3 pm"
    """
    # --- Pattern 1: relative time ("in X mins/hours") ---
    # Matches: remind (me) (again) in X min/mins/minute/minutes/hour/hours/hr/hrs
    # Also: snooze (for) X min/mins/...
    relative_pattern = (
        r'(?:remind(?:\s+me)?(?:\s+again)?|snooze)'
        r'(?:\s+(?:in|for|after))?\s+'
        r'(\d+(?:\.\d+)?)\s*'
        r'(min(?:ute)?s?|hrs?|hours?)\b'
    )
    match = re.search(relative_pattern, text)
    if match:
        amount = float(match.group(1))
        unit = match.group(2)
        if unit.startswith('h'):
            delay_seconds = int(amount * 3600)
            desc = f"in {amount:g} hour{'s' if amount != 1 else ''}"
        else:
            delay_seconds = int(amount * 60)
            desc = f"in {int(amount)} min{'s' if amount != 1 else ''}"
        return (delay_seconds, desc)

    # --- Pattern 2: absolute time ("at HH:MM am/pm" or "at HH:MM" 24h) ---
    absolute_pattern = (
        r'(?:remind(?:\s+me)?(?:\s+again)?)'
        r'\s+at\s+'
        r'(\d{1,2})(?::(\d{2}))?\s*'
        r'(am|pm)?'
    )
    match = re.search(absolute_pattern, text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)

        if ampm:
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0

        now = datetime.now(tz=TZ)
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If the target time already passed today, schedule for tomorrow
        if target <= now:
            target += timedelta(days=1)

        delay_seconds = int((target - now).total_seconds())
        time_str = target.strftime("%-I:%M %p")
        return (delay_seconds, f"at {time_str}")

    return None


async def send_custom_reminder(context) -> None:
    """Callback for one-time custom reminders."""
    try:
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text="⏰ *Reminder!* Time to drink some water! 💧",
            parse_mode="Markdown"
        )
        logger.info("Custom reminder sent successfully")
    except Exception as e:
        logger.error(f"Failed to send custom reminder: {e}")


@authorized_only
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all non-command text messages.

    Tries to parse a water intake amount from natural text.
    Supported patterns:
      - "drank 200 ml"
      - "200ml"
      - "200 ml"
      - "just had 300 ml"
      - "drank 500ml just now"
    
    If no number is found, replies with a hint.
    """
    text = update.message.text.strip().lower()
    
    # Check if this is a summary/status query (not an intake log)
    summary_keywords = ["how much", "total", "summary", "status", "progress", "lagging", "behind"]
    if any(keyword in text for keyword in summary_keywords):
        logger.info(f"Summary query: {text}")
        await update.message.reply_text(build_summary_text())
        return
    
    # Check if this is a custom reminder request
    reminder_result = parse_custom_reminder(text)
    if reminder_result is not None:
        delay_seconds, description = reminder_result
        # Schedule a one-time reminder
        context.job_queue.run_once(
            send_custom_reminder,
            when=delay_seconds,
            name=f"custom_{int(datetime.now().timestamp())}"
        )
        logger.info(f"Custom reminder scheduled: {description} ({delay_seconds}s from now)")
        await update.message.reply_text(f"⏰ Got it! I'll remind you {description}.")
        return
    
    # Try to find a number followed by optional "ml" (or just a bare number)
    # This regex looks for: any digits, optionally followed by whitespace + "ml"
    # Examples that match: "200", "200ml", "200 ml"
    match = re.search(r'(\d+)\s*ml\b', text)
    
    if not match:
        # Maybe they just typed a bare number like "200"
        match = re.search(r'\b(\d+)\b', text)
    
    if match:
        amount = int(match.group(1))
        
        # Sanity check: reject unreasonable values
        if amount <= 0 or amount > 5000:
            await update.message.reply_text(
                f"🤔 {amount} ml doesn't seem right. Please enter between 1 and 5000 ml."
            )
            return
        
        # Log to database
        time_str, total = log_water(amount)
        
        logger.info(f"Logged {amount} ml at {time_str}. Today's total: {total} ml")
        await update.message.reply_text(
            f"✅ Logged {amount} ml at {time_str}\n"
            f"📊 Today's total: {total} ml"
        )
    else:
        # No number found in the message
        await update.message.reply_text(
            "I didn't catch an amount. Try:\n"
            "• \"drank 200 ml\"\n"
            "• \"250ml\"\n"
            "• or just \"200\""
        )


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called automatically by JobQueue at each scheduled hour.

    This is NOT triggered by a user message — it's triggered by the clock.
    That's why it doesn't have an `update` parameter (no incoming message).
    Instead it uses `context.bot.send_message()` to proactively message you.

    Wrapped in try/except because APScheduler swallows job errors silently —
    they don't go through app.add_error_handler(). Without this try/except,
    a crash here would be completely invisible in logs.
    """
    try:
        logger.info("[REMINDER] send_reminder triggered")
        total = get_today_total()
        remaining = max(0, DAILY_TARGET_ML - total)

        if remaining == 0:
            message = "🎉 You've hit your water target for today! Keep it up."
        else:
            message = (
                f"💧 Time to drink water!\n\n"
                f"📊 Today so far: {total} ml / {DAILY_TARGET_ML} ml\n"
                f"🚩 Still need: {remaining} ml"
            )

        await context.bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"[REMINDER] Sent successfully: {total}/{DAILY_TARGET_ML} ml")
    except Exception as e:
        logger.error(f"[REMINDER] FAILED to send: {e}", exc_info=True)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any uncaught exceptions in handlers.

    Without this, errors get swallowed silently. This ensures:
    - The error is logged to bot.log (so you can debug later)
    - The bot doesn't crash — it keeps running for the next message
    """
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)


def main() -> None:
    """Create the bot application and start polling."""
    # Initialize database — creates the table if this is the first run
    init_db()
    logger.info("Database initialized (water.db)")

    app = Application.builder().token(BOT_TOKEN).build()

    # Register error handler
    app.add_error_handler(error_handler)

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("testreminder", test_reminder))

    # Message handler — catches any text that isn't a command
    # Tries to parse water intake or respond to natural queries
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ──────────────────────────────────────────────────────────────────────
    # HOURLY REMINDER (JobQueue)
    # ──────────────────────────────────────────────────────────────────────
    # How this works:
    #
    # 1. `job_queue` is a scheduler built into python-telegram-bot.
    #    It uses APScheduler under the hood.
    #
    # 2. `run_daily()` means: "run this function once per day at a specific time."
    #    We call it multiple times — once for EACH hour we want a reminder.
    #
    # 3. For example, if WAKE_HOUR=7 and SLEEP_HOUR=23, we schedule reminders
    #    at 07:00, 08:00, 09:00, ... 22:00 (16 reminders per day).
    #
    # 4. The `send_reminder` function runs at each scheduled time.
    #    It sends you a Telegram message with today's progress.
    #
    # 5. These jobs survive as long as the bot process is running.
    #    If you restart the bot, they're re-registered automatically.
    #
    # Why run_daily() instead of run_repeating(interval=3600)?
    #   - run_repeating starts from NOW, so reminders come at random minutes
    #     (e.g., if you start at 14:37, reminders at 15:37, 16:37...)
    #   - run_daily at exact hours gives clean :00 reminders
    #   - Also easier to restrict to waking hours
    # ──────────────────────────────────────────────────────────────────────

    job_queue = app.job_queue

    for hour in range(WAKE_HOUR, SLEEP_HOUR):
        # Schedule one reminder per hour, at HH:00:00 in YOUR timezone
        # tzinfo=TZ is critical — without it, APScheduler assumes UTC
        # and your 7:00 AM reminder would fire at 12:30 PM IST instead
        reminder_time = dt_time(hour=hour, minute=0, second=0, tzinfo=TZ)
        job_queue.run_daily(
            send_reminder,           # The function to call
            time=reminder_time,      # When to call it (e.g., 07:00)
            name=f"reminder_{hour}"  # A label (useful for debugging)
        )

    print(f"[OK] Hourly reminders scheduled: {WAKE_HOUR}:00 to {SLEEP_HOUR - 1}:00")
    logger.info("Bot started successfully")
    logger.info(f"Authorized chat ID: {CHAT_ID}")
    logger.info(f"Daily target: {DAILY_TARGET_ML} ml")
    logger.info(f"Reminders: {WAKE_HOUR}:00 to {SLEEP_HOUR - 1}:00")
    # drop_pending_updates=True → ignore old messages from when bot was offline
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
