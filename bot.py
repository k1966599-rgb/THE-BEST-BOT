import asyncio
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from src.bot_interface.handlers import start, button, load_bot_state
from src.background_scanner import run_scanner
from src.utils.config_loader import config

# --- Configuration ---
TELEGRAM_TOKEN = config['telegram']['token']

async def main() -> None:
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
    is_running = load_bot_state()
    application.bot_data['is_running'] = is_running
    if is_running:
        print("Bot was running previously. Restarting background scanner...")
        asyncio.create_task(run_scanner(application))

    print("Bot is running... Press Ctrl-C to stop.")
    # Run the bot until the user presses Ctrl-C
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
