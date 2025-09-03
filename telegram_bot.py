import logging
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Import the analysis engine and config
from config import get_config, WATCHLIST
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

def get_start_message_text() -> str:
    """Creates the new, elaborate start message text."""
    config = get_config()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "🟢 متصل وجاهز للعمل" if bot_state["is_active"] else "🔴 متوقف"
    platform = config['trading'].get('EXCHANGE_ID', 'N/A').upper()

    text = (
        "╔═══════════════════════════════════════╗\n"
        "║            💎 THE BEST BOT 💎           ║\n"
        "║         🎯 نظام التحليل الفني المتقدم 🎯         ║\n"
        "╚═══════════════════════════════════════╝\n\n"
        f"🕐 **التوقيت:** {current_time}\n"
        f"📶 **حالة النظام:** {status}\n"
        f"🌐 **المنصة:** 🏛️ {platform} Exchange\n\n"
        "═══════════════════════════════════════\n\n"
        "📋 **الخدمات المتوفرة:**\n\n"
        "🔍 **التحليل الفني الشامل** ⚡\n"
        "   💰 تحليل أكبر 20 عملة رقمية\n"
        "   ⏰ 7 إطارات زمنية مختلفة\n"
        "   📈 مؤشرات فنية متقدمة\n\n"
        "📊 **أدوات التحليل:** 🛠️\n"
        "   🌟 نسب فيبوناتشي\n"
        "   🔴 الدعوم والمقاومات\n"
        "   📉 القنوات السعرية\n"
        "   🏛️ النماذج الكلاسيكية\n"
        "   🎯 مناطق العرض والطلب\n\n"
        "🎯 **التوصيات الذكية:** 🧠\n"
        "   ✅ نقاط الدخول المثالية\n"
        "   🛑 مستويات وقف الخسارة\n"
        "   💵 أهداف الربح المحسوبة\n"
        "   ⚖️ إدارة المخاطر\n\n"
        "═══════════════════════════════════════\n\n"
        "🚀 **البوت جاهز للاستخدام** 🤖\n"
        "📱 استخدم الأزرار أدناه للتفاعل مع النظام 👇\n\n"
        "💡 **نصيحة:** 📝 للحصول على أفضل النتائج،\n"
        "راجع التحليلات بانتظام وتابع تطورات السوق 📊\n\n"
        "╔═══════════════════════════════════════╗\n"
        "║  🔥 مرحباً بك في أقوى نظام تحليل فني 🔥  ║\n"
        "╚═══════════════════════════════════════╝"
    )
    return text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text(
        text=get_start_message_text(),
        reply_markup=get_main_keyboard(),
        parse_mode='HTML' # Using HTML for the bolding and other formatting
    )

async def main_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for all button presses."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "start_menu":
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    elif callback_data == "start_bot":
        bot_state["is_active"] = True
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    elif callback_data == "stop_bot":
        bot_state["is_active"] = False
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='HTML')

    elif callback_data == "analyze_menu":
        if not bot_state["is_active"]:
            await query.message.reply_text("البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.")
            return
        await query.edit_message_text(text="الرجاء اختيار عملة للتحليل:", reply_markup=get_coin_list_keyboard())

    elif callback_data.startswith("coin_"):
        symbol = callback_data.split("_", 1)[1]
        await query.edit_message_text(text=f"جاري تحليل {symbol}، قد يستغرق هذا بعض الوقت...")

        try:
            config = get_config()
            final_report = get_ranked_analysis_for_symbol(symbol, config)
            send_telegram_message(final_report)
            await query.message.reply_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error during analysis for {symbol}: {e}")
            await query.message.reply_text(f"حدث خطأ أثناء تحليل {symbol}. يرجى المحاولة مرة أخرى.")

def main() -> None:
    """Main function to run the bot."""
    config = get_config()
    token = config['telegram']['BOT_TOKEN']
    if not token:
        logger.error("Error: Telegram bot token not found in .env file.")
        return

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(main_button_callback))

    logger.info("Interactive bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
