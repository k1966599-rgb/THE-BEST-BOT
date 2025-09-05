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
from run_bot import get_ranked_analysis_for_symbol
from telegram_sender import send_telegram_message
from okx_data import OKXDataFetcher

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

def get_coin_list_keyboard() -> InlineKeyboardMarkup:
    """Creates the keyboard for coin selection."""
    keyboard = [
        [InlineKeyboardButton(coin, callback_data=f"coin_{coin}") for coin in WATCHLIST[i:i+2]]
        for i in range(0, len(WATCHLIST), 2)
    ]
    # Add the back button to return to the main menu
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="start_menu")])
    return InlineKeyboardMarkup(keyboard)

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

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    # Display the new welcome message and main menu
    await update.message.reply_text(
        text=get_welcome_message(),
        reply_markup=get_main_keyboard(),
        parse_mode='HTML'
    )

async def main_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for all button presses."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "start_menu":
        await query.edit_message_text(text=get_welcome_message(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    elif callback_data == "start_bot":
        bot_state["is_active"] = True
        await query.edit_message_text(text=get_welcome_message(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    elif callback_data == "stop_bot":
        bot_state["is_active"] = False
        await query.edit_message_text(text=get_welcome_message(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    elif callback_data == "analyze_menu":
        if not bot_state["is_active"]:
            await query.message.reply_text("البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.")
            return
        await query.edit_message_text(text="الرجاء اختيار عملة للتحليل:", reply_markup=get_coin_list_keyboard())

    elif callback_data.startswith("coin_"):
        symbol = callback_data.split("_", 1)[1]
        # Now, instead of analyzing, show the analysis type selection keyboard
        await query.edit_message_text(
            text=f"اختر نوع التحليل للعملة {symbol}:",
            reply_markup=get_analysis_type_keyboard(symbol)
        )

    elif callback_data.startswith(("long_", "medium_", "short_")):
        parts = callback_data.split("_", 1)
        analysis_type = parts[0]
        symbol = parts[1]

        timeframe_map = {
            "long": ['1d', '4h', '1h'],
            "medium": ['30m', '15m'],
            "short": ['5m', '3m', '1m']
        }
        timeframes_to_analyze = timeframe_map.get(analysis_type)

        if not timeframes_to_analyze:
            await query.message.reply_text("نوع تحليل غير صالح.")
            return

        await query.edit_message_text(text=f"جاري تحليل {symbol} لـ {analysis_type}، قد يستغرق هذا بعض الوقت...")

        try:
            config = get_config()
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

def main() -> None:
    """Main function to run the bot."""
    config = get_config()
    token = config['telegram']['BOT_TOKEN']
    if not token:
        logger.error("Error: Telegram bot token not found in .env file.")
        return

    # Initialize the data fetcher
    logger.info("🚀 Initializing OKX Data Fetcher for the interactive bot...")
    okx_fetcher = OKXDataFetcher()

    # The symbols to track can be taken from the watchlist
    okx_symbols = list(set([s.replace('/', '-') for s in WATCHLIST]))

    logger.info(f"📡 Starting data collection for {len(okx_symbols)} symbols...")
    fetcher_thread = threading.Thread(target=okx_fetcher.start_full_data_collection, args=(okx_symbols,), daemon=True)
    fetcher_thread.start()

    logger.info("⏳ Waiting 2 seconds for initial data from WebSocket...")
    time.sleep(2)

    application = Application.builder().token(token).build()

    # Store the fetcher instance in the application context
    application.bot_data['okx_fetcher'] = okx_fetcher

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(main_button_callback))

    logger.info("Interactive bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
