import os
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from src.bot_interface.handlers import start, button

# --- Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def main() -> None:
    """Sets up and starts the Telegram bot."""
    if not TELEGRAM_TOKEN:
        print("FATAL: TELEGRAM_TOKEN environment variable not set.")
        return

    print("Starting bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register the command and button handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    print("Bot is running... Press Ctrl-C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
