import asyncio
import signal
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from src.bot_interface.handlers import start, button, load_bot_state
from src.background_scanner import run_scanner
from src.utils.config_loader import config

# --- Configuration ---
TELEGRAM_TOKEN = config['telegram']['token']

async def main() -> None:
    """Sets up and starts the Telegram bot with graceful shutdown."""
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
        # Register the command and button handlers
        application.add_handler(CommandHandler("start", start))
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
