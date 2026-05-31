"""
Water Reminder Bot — Step 9
Replaced echo handler with natural text parser for water intake logging.
Messages like "drank 200 ml", "250ml", "just had 300 ml" now get logged.
"""

import os
import re
from functools import wraps

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler

from database import init_db, log_water, get_today_total

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))  # Convert to int for comparison


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
            # Log the unauthorized attempt (visible in your terminal)
            print(f"[BLOCKED] Unauthorized user {update.effective_user.id} tried: {update.message.text}")
            return  # Silently ignore — don't even reply
        return await func(update, context)
    wrapper = wraps(func)(wrapper)
    return wrapper


@authorized_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command. Sends a welcome message."""
    print(f"[OK] /start from {update.effective_user.first_name}")
    await update.message.reply_text(
        "Hey! I'm your Water Reminder Bot 💧\n\n"
        "I'll remind you to drink water every hour and track your intake.\n\n"
        "Try sending: drank 200 ml\n"
        "Or type /help for all commands."
    )


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
        
        print(f"[OK] Logged {amount} ml at {time_str}. Today's total: {total} ml")
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


def main() -> None:
    """Create the bot application and start polling."""
    # Initialize database — creates the table if this is the first run
    init_db()
    print("[OK] Database initialized (water.db)")

    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Message handler — catches any text that isn't a command
    # Tries to parse water intake from natural text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running... Press Ctrl+C to stop.")
    print(f"Authorized chat ID: {CHAT_ID}")
    print("Handlers registered: /start, text messages")
    # drop_pending_updates=True → ignore old messages from when bot was offline
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
