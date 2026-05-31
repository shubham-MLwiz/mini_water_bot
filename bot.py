"""
Water Reminder Bot — Step 6
Minimal bot that responds to /start command.
This proves the token works and you can talk to your bot.
"""

import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables from .env file
# This reads BOT_TOKEN, CHAT_ID, etc. into os.environ
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command. Sends a welcome message."""
    await update.message.reply_text(
        "Hey! I'm your Water Reminder Bot 💧\n\n"
        "I'll remind you to drink water every hour and track your intake.\n\n"
        "Try sending: drank 200 ml\n"
        "Or type /help for all commands."
    )


def main() -> None:
    """Create the bot application and start polling."""
    # Build the Application with your bot token
    app = Application.builder().token(BOT_TOKEN).build()

    # Register the /start command handler
    # When someone sends "/start", the `start` function above gets called
    app.add_handler(CommandHandler("start", start))

    # Start polling — the bot keeps asking Telegram "any new messages?"
    # This runs forever until you press Ctrl+C
    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
