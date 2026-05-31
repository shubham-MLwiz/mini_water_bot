"""
Water Reminder Bot — Step 7
Added chat ID restriction: only YOUR Telegram account can use this bot.
Anyone else who messages it gets silently ignored.
"""

import os
from functools import wraps

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler

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
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Temporary handler: echoes back any text message.

    This will be replaced by the water intake parser in Step 9.
    For now it proves that the bot receives and processes your messages.
    """
    text = update.message.text
    print(f"[OK] Message received: {text}")
    await update.message.reply_text(f"Got it: \"{text}\"\n(Intake parsing coming in Step 9)")


def main() -> None:
    """Create the bot application and start polling."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))

    # Message handler — catches any text that isn't a command
    # filters.TEXT = only text messages (not photos, stickers, etc.)
    # ~filters.COMMAND = exclude messages starting with / (those go to CommandHandler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Bot is running... Press Ctrl+C to stop.")
    print(f"Authorized chat ID: {CHAT_ID}")
    print("Handlers registered: /start, text messages")
    # drop_pending_updates=True → ignore old messages from when bot was offline
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
