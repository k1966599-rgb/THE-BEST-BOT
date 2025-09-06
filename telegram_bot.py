import logging
import os
import re
from datetime import datetime
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import the analysis engine and config
from config import get_config, WATCHLIST
from run_bot import get_ranked_analysis_for_symbol
from telegram_sender import send_telegram_message
from okx_data import OKXDataFetcher

# --- Security: Add logging filter to hide token ---
class TokenFilter(logging.Filter):
    """A filter to hide the bot token from log records."""
    def filter(self, record):
        if hasattr(record, 'msg'):
            # This regex is a bit broad but should catch the token in URLs
            record.msg = re.sub(r'bot(\d+):[A-Za-z0-9_-]+', r'bot\1:***TOKEN_REDACTED***', str(record.msg))
        return True

# Setup basic logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
# Get the root logger and add the filter to all its handlers
for handler in logging.root.handlers:
    handler.addFilter(TokenFilter())
# Reduce noise from the HTTPX library, which logs every API call including the URL with the token
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

bot_state = {"is_active": True}
okx_fetcher = None # Global fetcher instance
data_fetcher_thread = None # Global thread for the fetcher

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for the /start command.
    Now directly triggers a default analysis and sends the report.
    """
    symbol = "BTC/USDT"
    analysis_type = "long"
    analysis_name = "استثمار طويل المدى (1D - 4H - 1H)"

    await update.message.reply_text(
        text=f"أهلاً بك في THE BEST BOT! 💎\n\n"
             f"جاري إعداد <b>{analysis_name}</b> للعملة الافتراضية <code>{symbol}</code>... قد يستغرق هذا بعض الوقت.",
        parse_mode='HTML'
    )

    try:
        config = get_config()
        timeframes = config['trading']['TIMEFRAME_GROUPS'].get(analysis_type)
        if not timeframes:
            await update.message.reply_text(f"خطأ: لم يتم العثور على مجموعة الإطارات الزمنية لـ {analysis_type}")
            return

        # Running the analysis in a separate thread to avoid blocking the bot
        def analysis_thread():
            try:
                final_report = get_ranked_analysis_for_symbol(symbol, config, okx_fetcher, timeframes, analysis_name)
                # Split the report into chunks if it's too long
                for i in range(0, len(final_report), 4096):
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=final_report[i:i + 4096],
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"Error in analysis thread for {symbol}: {e}", exc_info=True)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"حدث خطأ فادح أثناء تحليل {symbol}. يرجى مراجعة السجلات."
                )

        # Start the thread
        thread = threading.Thread(target=analysis_thread)
        thread.start()

    except Exception as e:
        logger.error(f"Error initiating analysis for {symbol}: {e}", exc_info=True)
        await update.message.reply_text(f"حدث خطأ قبل بدء تحليل {symbol}. يرجى المحاولة مرة أخرى.")

def run_fetcher_service():
    """Function to run in a separate thread to manage the data fetcher."""
    global okx_fetcher
    
    okx_symbols = [s.replace('/', '-') for s in WATCHLIST]
    okx_fetcher.start_data_services(okx_symbols)
    # Keep the thread alive while the fetcher is running
    while not threading.main_thread().is_alive():
        time.sleep(1)
    okx_fetcher.stop()
    logger.info("OKX Data Fetcher stopped.")

def main() -> None:
    """Main function to run the bot."""
    global okx_fetcher, data_fetcher_thread
    config = get_config()
    token = config['telegram']['BOT_TOKEN']
    if not token:
        logger.error("CRITICAL: Telegram bot token not found in .env file. The bot cannot start.")
        return

    # Initialize and start the data fetcher
    logger.info("🚀 Initializing OKX Data Fetcher...")
    okx_fetcher = OKXDataFetcher()
    
    data_fetcher_thread = threading.Thread(target=run_fetcher_service, daemon=True)
    data_fetcher_thread.start()
    
    logger.info("⏳ Waiting 5 seconds for initial data...")
    time.sleep(5)

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))

    try:
        logger.info("🤖 Interactive bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutdown requested.")
    finally:
        logger.info("⏹️ Stopping bot and data fetcher...")

if __name__ == "__main__":
    import time
    main()
