import logging
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import get_config

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

bot_state = {"is_active": True}

def get_keyboard() -> InlineKeyboardMarkup:
    """Creates the interactive keyboard with the updated button text."""
    keyboard = [
        [
            InlineKeyboardButton("▶️ تشغيل", callback_data="start_bot"),
            InlineKeyboardButton("⏹️ إيقاف", callback_data="stop_bot"),
        ],
        [InlineKeyboardButton("🔍 تحليل", callback_data="analyze")],
    ]
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    user = update.effective_user
    logger.info(f"User {user.first_name} started the bot.")

    # The initial "Welcome" message is now part of the main message.
    # We send the main message directly.
    await update.message.reply_text(
        text=get_start_message_text(),
        reply_markup=get_keyboard(),
        parse_mode='Markdown' # Using Markdown for the bolding
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for button presses."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    logger.info(f"Button pressed: {callback_data}")

    if callback_data == "start_bot":
        bot_state["is_active"] = True
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_keyboard(), parse_mode='Markdown')
    elif callback_data == "stop_bot":
        bot_state["is_active"] = False
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_keyboard(), parse_mode='Markdown')
    elif callback_data == "analyze":
        if not bot_state["is_active"]:
            await query.message.reply_text("البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.")
            return
        # This will be implemented in the next phase
        await query.message.reply_text("ميزة التحليل قيد التطوير وسيتم إضافتها في المرحلة التالية.")

def main() -> None:
    """Main function to run the bot."""
    config = get_config()
    token = config['telegram']['BOT_TOKEN']
    if not token:
        logger.error("Error: Telegram bot token not found in .env file.")
        return

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Interactive bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
