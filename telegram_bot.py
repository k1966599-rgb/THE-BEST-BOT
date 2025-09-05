import logging
import os
from datetime import datetime
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import the analysis engine and config
from config import get_config, WATCHLIST
from run_bot import get_ranked_analysis_for_symbol
from telegram_sender import send_telegram_message
from okx_data import OKXDataFetcher
from report_generator import escape_markdown_v2

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

bot_state = {"is_active": True}
okx_fetcher = None # Global fetcher instance
data_fetcher_thread = None # Global thread for the fetcher

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Creates the main interactive keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("▶️ تشغيل", callback_data="start_bot"),
            InlineKeyboardButton("⏹️ إيقاف", callback_data="stop_bot"),
        ],
        [InlineKeyboardButton("🔍 تحليل", callback_data="analyze_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_coin_list_keyboard() -> InlineKeyboardMarkup:
    """Creates the keyboard for coin selection."""
    keyboard = [
        [InlineKeyboardButton(coin, callback_data=f"coin_{coin}") for coin in WATCHLIST[i:i+2]]
        for i in range(0, len(WATCHLIST), 2)
    ]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="start_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_start_message_text() -> str:
    """Creates the new, elaborate start message text."""
    config = get_config()
    # Using a fixed date for the welcome message as requested by the user
    current_time = "2025-09-05 08:14:10"
    status = "🟢 متصل وجاهز للعمل" if bot_state["is_active"] else "🔴 متوقف"
    platform = config['trading'].get('EXCHANGE_ID', 'OKX').upper()

    # This is the user's requested format, using MarkdownV2 syntax
    text = (
        f"💎 *THE BEST BOT* 💎\n"
        f"🎯 *نظام التحليل الفني المتقدم* 🎯\n\n"
        f"🕐 *التوقيت:* `{current_time}`\n"
        f"📶 *حالة النظام:* {status}\n"
        f"🌐 *المنصة:* 🏛️ {platform} Exchange\n\n"
        f"*📋 الخدمات المتوفرة:*\n\n"
        f"🔍 التحليل الفني الشامل ⚡️\n"
        f"💰 تحليل أكبر 20 عملة رقمية\n"
        f"⏰ 7 إطارات زمنية مختلفة\n"
        f"📈 مؤشرات فنية متقدمة\n\n"
        f"*📊 أدوات التحليل: 🛠️*\n"
        f"🌟 نسب فيبوناتشي\n"
        f"🔴 الدعوم والمقاومات\n"
        f"📉 القنوات السعرية\n"
        f"🏛️ النماذج الكلاسيكية\n"
        f"🎯 مناطق العرض والطلب\n\n"
        f"*🎯 التوصيات الذكية: 🧠*\n"
        f"✅ نقاط الدخول المثالية\n"
        f"🛑 مستويات وقف الخسارة\n"
        f"💵 أهداف الربح المحسوبة\n"
        f"⚖️ إدارة المخاطر"
    )
    return text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text(
        text=get_start_message_text(),
        reply_markup=get_main_keyboard(),
        parse_mode='MarkdownV2'
    )

def get_analysis_timeframe_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """Creates the keyboard for selecting the analysis timeframe."""
    keyboard = [
        [InlineKeyboardButton("تحليل طويل المدى (يومي, 4س, 1س)", callback_data=f"analyze_long_{symbol}")],
        [InlineKeyboardButton("تحليل متوسط المدى (30د, 15د)", callback_data=f"analyze_medium_{symbol}")],
        [InlineKeyboardButton("تحليل قصير المدى (5د, 3د)", callback_data=f"analyze_short_{symbol}")],
        [InlineKeyboardButton("🔙 رجوع لقائمة العملات", callback_data="analyze_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def main_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for all button presses."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "start_menu":
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='MarkdownV2')

    elif callback_data == "start_bot":
        bot_state["is_active"] = True
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='MarkdownV2')

    elif callback_data == "stop_bot":
        bot_state["is_active"] = False
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='MarkdownV2')

    elif callback_data == "analyze_menu":
        if not bot_state["is_active"]:
            await query.message.reply_text("البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.")
            return
        await query.edit_message_text(text="الرجاء اختيار عملة للتحليل:", reply_markup=get_coin_list_keyboard())

    elif callback_data.startswith("coin_"):
        symbol = callback_data.split("_", 1)[1]
        safe_symbol = escape_markdown_v2(symbol)
        await query.edit_message_text(
            text=f"اختر نوع التحليل لـ `{safe_symbol}`:",
            reply_markup=get_analysis_timeframe_keyboard(symbol),
            parse_mode='MarkdownV2'
        )

    elif callback_data.startswith("analyze_"):
        parts = callback_data.split("_")
        analysis_type = parts[1]
        symbol = "_".join(parts[2:])
        safe_symbol = escape_markdown_v2(symbol)

        analysis_type_map = {
            "long": "استثمار طويل المدى (1D - 4H - 1H)",
            "medium": "تداول متوسط المدى (30m - 15m)",
            "short": "مضاربة سريعة (5m - 3m)"
        }
        analysis_name = analysis_type_map.get(analysis_type, "غير محدد")

        await query.edit_message_text(
            text=f"جاري إعداد *{escape_markdown_v2(analysis_name)}* لـ `{safe_symbol}`\.\.\. قد يستغرق هذا بعض الوقت\.",
            parse_mode='MarkdownV2'
        )

        try:
            config = get_config()
            timeframes = config['trading']['TIMEFRAME_GROUPS'].get(analysis_type)
            if not timeframes:
                await query.message.reply_text(f"خطأ: لم يتم العثور على مجموعة الإطارات الزمنية لـ {analysis_type}")
                return

            # Call the analysis function with the correct timeframes and analysis name
            final_report = get_ranked_analysis_for_symbol(symbol, config, okx_fetcher, timeframes, analysis_name)

            # The report generator is now fully implemented.
            await query.message.reply_text(text=final_report, parse_mode='MarkdownV2')

            # Return to the main menu
            await query.message.reply_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='MarkdownV2')
        except Exception as e:
            logger.error(f"Error during analysis for {symbol}: {e}")
            await query.message.reply_text(f"حدث خطأ أثناء تحليل {symbol}. يرجى المحاولة مرة أخرى.")

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
        logger.error("Error: Telegram bot token not found in .env file.")
        return

    # Initialize and start the data fetcher
    logger.info("🚀 Initializing OKX Data Fetcher...")
    okx_fetcher = OKXDataFetcher()

    # Run the fetcher in a background thread
    data_fetcher_thread = threading.Thread(target=run_fetcher_service, daemon=True)
    data_fetcher_thread.start()

    logger.info("⏳ Waiting 5 seconds for initial data...")
    time.sleep(5)

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(main_button_callback))

    try:
        logger.info("🤖 Interactive bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot shutdown requested.")
    finally:
        logger.info("⏹️ Stopping bot and data fetcher...")
        # The fetcher thread is a daemon, so it will exit automatically.
        # If it were not a daemon, we'd need a more complex shutdown mechanism.

if __name__ == "__main__":
    import time
    main()
