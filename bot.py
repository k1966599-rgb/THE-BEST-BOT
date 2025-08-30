import asyncio
import signal
import fcntl
import sys
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

# --- Single Instance Lock ---
# This ensures that only one instance of the bot can run at a time.
try:
    lock_file = open('/tmp/trading_bot.lock', 'w')
    fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("البوت شغال فعلاً! (Another instance is already running.)")
    sys.exit(1)
# ---

from src.bot_interface.handlers import (
    start, button, load_bot_state,
    add_symbol_start, add_symbol_receive, cancel_conversation,
    AWAITING_SYMBOL_TO_ADD
)
from src.background_scanner import run_scanner
from src.utils.config_loader import load_config

# --- Configuration ---

async def main() -> None:
    """Sets up and starts the Telegram bot with graceful shutdown."""
    config = load_config()
    TELEGRAM_TOKEN = config.get('telegram', {}).get('token')

    if not TELEGRAM_TOKEN:
        print("FATAL: TELEGRAM_TOKEN is not configured. Please check your .env file.")
        return

    print("Starting bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- Graceful Shutdown Handler ---
    # This will allow us to stop the bot cleanly with Ctrl+C
    loop = asyncio.get_running_loop()
    stop_signals = (signal.SIGINT, signal.SIGTERM)
    for sig in stop_signals:
        loop.add_signal_handler(
            sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, application))
        )

    try:
        # --- Handler Registration ---

        # Conversation handler for adding a symbol
        add_symbol_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(add_symbol_start, pattern='^add_symbol_start$')],
            states={
                AWAITING_SYMBOL_TO_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_symbol_receive)],
            },
            fallbacks=[CommandHandler('cancel', cancel_conversation)],
            # We use per_user and per_chat persistence to make this more robust
            # across bot restarts if the user is in the middle of a conversation.
            name="add_symbol_conversation",
            persistent=False,
        )
        application.add_handler(add_symbol_conv)

        # Regular command and button handlers
        application.add_handler(CommandHandler("start", start))
        # The main button handler should be after specific callback handlers
        application.add_handler(CallbackQueryHandler(button))

        # Initialize the application
        await application.initialize()
        await application.start()

        # Start polling for updates from Telegram
        await application.updater.start_polling()
        print("Bot is polling...")

        # Check for persisted state and start the background scanner if needed
        if load_bot_state():
            print("Bot was running previously. Starting background scanner...")
            application.bot_data['is_running'] = True
            asyncio.create_task(run_scanner(application))

        # Keep the application running until a stop signal is received
        # This replaces the blocking run_polling() call
        while application.running:
            await asyncio.sleep(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Bot shutting down...")
        # The shutdown is now handled by the signal handler,
        # but we can add extra cleanup here if needed.
        if application.running:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

async def shutdown(signal, loop, application):
    """Gracefully stop the application and scanner."""
    print(f"Received stop signal {signal}... Shutting down gracefully.")

    # Stop the background scanner if it's running
    if 'scanner_task' in application.bot_data and application.bot_data['scanner_task']:
        application.bot_data['scanner_task'].cancel()
        try:
            await application.bot_data['scanner_task']
        except asyncio.CancelledError:
            print("Scanner task successfully cancelled.")

    # Stop the Telegram bot application
    if application.running:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

    # Stop the event loop
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
