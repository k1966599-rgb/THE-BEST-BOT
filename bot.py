import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from src.bot_interface.handlers import start, button, initialize_bot_state
from src.utils.config_loader import config

# --- Configuration ---
TELEGRAM_TOKEN = config['telegram']['token']

def main() -> None:
    """Sets up and starts the Telegram bot."""
    if not TELEGRAM_TOKEN:
        print("FATAL: TELEGRAM_TOKEN is not configured. Please check your .env file.")
        return

    print("Starting bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register the command and button handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    # Check for persisted state and start scanner if needed
    initialize_bot_state(application)

    print("Bot is running... Press Ctrl-C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
