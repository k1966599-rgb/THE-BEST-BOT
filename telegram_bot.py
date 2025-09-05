import logging
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import the analysis engine and config
from config import get_config, WATCHLIST
# Note: The interactive part of the bot that calls get_ranked_analysis_for_symbol
# will need a larger refactor to get access to the okx_fetcher instance.
# This is a known limitation for now.
import time
import threading
import concurrent.futures
from okx_data import OKXDataFetcher
from run_bot import get_ranked_analysis_for_symbol
from telegram_sender import send_telegram_message

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

bot_state = {"is_active": True}

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

def get_welcome_message() -> str:
    """Creates the new welcome message text based on the user's template."""
    config = get_config()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "🟢 متصل وجاهز للعمل" if bot_state["is_active"] else "🔴 متوقف"
    platform = config['trading'].get('EXCHANGE_ID', 'N/A').upper()

    text = (
        "💎 THE BEST BOT 💎\n"
        "🎯 نظام التحليل الفني المتقدم 🎯\n\n"
        f"🕐 التوقيت: {current_time}\n"
        f"📶 حالة النظام: {status}\n"
        f"🌐 المنصة: 🏛️ {platform} Exchange\n\n"
        "📋 الخدمات المتوفرة:\n\n"
        "🔍 التحليل الفني الشامل ⚡️\n"
        "💰 تحليل أكبر 20 عملة رقمية\n"
        "⏰ 7 إطارات زمنية مختلفة\n"
        "📈 مؤشرات فنية متقدمة\n\n"
        "📊 أدوات التحليل: 🛠️\n"
        "🌟 نسب فيبوناتشي\n"
        "🔴 الدعوم والمقاومات\n"
        "📉 القنوات السعرية\n"
        "🏛️ النماذج الكلاسيكية\n"
        "🎯 مناطق العرض والطلب\n\n"
        "🎯 التوصيات الذكية: 🧠\n"
        "✅ نقاط الدخول المثالية\n"
        "🛑 مستويات وقف الخسارة\n"
        "💵 أهداف الربح المحسوبة\n"
        "⚖️ إدارة المخاطر\n\n"
        "🚀 البوت جاهز للاستخدام 🤖\n"
        "📱 استخدم الأزرار أدناه للتفاعل مع النظام 👇\n\n"
        "💡 نصيحة: 📝 للحصول على أفضل النتائج،\n"
        "راجع التحليلات بانتظام وتابع تطورات السوق 📊\n\n"
        "🔥 مرحباً بك في أقوى نظام تحليل فني 🔥"
    )
    return text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text(
        text=get_welcome_message(),
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

def get_analysis_type_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """Creates the keyboard for selecting the analysis type."""
    keyboard = [
        [
            InlineKeyboardButton("- صفقة طويلة المدى -", callback_data=f"long_{symbol}"),
        ],
        [
            InlineKeyboardButton("- متوسطة المدى -", callback_data=f"medium_{symbol}"),
        ],
        [
            InlineKeyboardButton("- مضاربة سريعة -", callback_data=f"short_{symbol}"),
        ],
        [
            InlineKeyboardButton("🔙 رجوع لقائمة العملات", callback_data="analyze_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- Callback Handlers ---

async def handle_start_menu(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    await query.edit_message_text(text=get_welcome_message(), reply_markup=get_main_keyboard(), parse_mode='HTML')

async def handle_bot_status_change(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, is_active: bool):
    bot_state["is_active"] = is_active
    await query.edit_message_text(text=get_welcome_message(), reply_markup=get_main_keyboard(), parse_mode='HTML')

async def handle_analyze_menu(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    if not bot_state["is_active"]:
        await query.answer("البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.", show_alert=True)
        return
    await query.edit_message_text(text="الرجاء اختيار عملة للتحليل:", reply_markup=get_coin_list_keyboard())

async def handle_coin_selection(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    symbol = query.data.split("_", 1)[1]
    await query.edit_message_text(
        text=f"اختر نوع التحليل للعملة {symbol}:",
        reply_markup=get_analysis_type_keyboard(symbol)
    )

async def handle_analysis_request(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE):
    parts = query.data.split("_", 1)
    analysis_type, symbol = parts[0], parts[1]

    config = get_config()
    timeframe_map = config['trading'].get('TIMEFRAME_GROUPS', {})
    timeframes_to_analyze = timeframe_map.get(analysis_type)

    if not timeframes_to_analyze:
        await query.message.reply_text("نوع تحليل غير صالح.")
        return

    await query.edit_message_text(text=f"جاري تحليل {symbol} لـ {analysis_type}، قد يستغرق هذا بعض الوقت...")

    try:
        okx_fetcher = context.bot_data.get('okx_fetcher')
        if not okx_fetcher:
            raise ValueError("OKX Fetcher not found in bot context.")

        final_report = get_ranked_analysis_for_symbol(
            symbol=symbol,
            config=config,
            okx_fetcher=okx_fetcher,
            timeframes_to_analyze=timeframes_to_analyze
        )
        send_telegram_message(final_report)
        await query.edit_message_text(text=get_welcome_message(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error during {analysis_type} analysis for {symbol}: {e}")
        await query.message.reply_text(f"حدث خطأ أثناء تحليل {symbol}. يرجى المحاولة مرة أخرى.")

# --- Main Callback Router ---

async def main_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for all button presses, routing to the correct sub-handler."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Map prefixes to their handler functions
    # Order matters: more specific prefixes should come first.
    handler_map = {
        "long_": handle_analysis_request,
        "medium_": handle_analysis_request,
        "short_": handle_analysis_request,
        "coin_": handle_coin_selection,
        "analyze_menu": handle_analyze_menu,
        "start_menu": handle_start_menu,
        "start_bot": lambda q, c: handle_bot_status_change(q, c, is_active=True),
        "stop_bot": lambda q, c: handle_bot_status_change(q, c, is_active=False),
    }

    for prefix, handler in handler_map.items():
        if callback_data.startswith(prefix):
            await handler(query, context)
            return

    logger.warning(f"No handler found for callback data: {callback_data}")

def main() -> None:
    """Main function to run the bot."""
    config = get_config()
    token = config['telegram']['BOT_TOKEN']
    if not token:
        logger.error("Error: Telegram bot token not found in .env file.")
        return

    logger.info("🚀 Initializing OKX Data Fetcher for the interactive bot...")
    okx_fetcher = OKXDataFetcher()

    def preload_data():
        """Fetches and caches all required historical data in the background."""
        logger.info("⏳ Starting background pre-loading of all historical data...")
        symbols_to_preload = list(set([s.replace('/', '-') for s in WATCHLIST]))

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # We use map to fetch data for all symbols in parallel.
            # The fetch function now uses caching, so this will only fetch if not already cached.
            executor.map(okx_fetcher.fetch_historical_data, symbols_to_preload)

        logger.info("✅ Background pre-loading of historical data complete.")

    preload_thread = threading.Thread(target=preload_data, daemon=True)
    preload_thread.start()

    application = Application.builder().token(token).build()
    application.bot_data['okx_fetcher'] = okx_fetcher

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(main_button_callback))

    logger.info("Interactive bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
