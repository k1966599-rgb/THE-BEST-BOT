import logging
import os
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# استيراد الإعدادات
from config import get_config

# إعداد تسجيل الدخول (Logging) لتتبع أداء البوت
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# إدارة حالة البوت (بشكل بسيط في هذه المرحلة)
bot_state = {"is_active": True}

# --- وظائف بناء الرسائل والأزرار ---

def get_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة الأزرار التفاعلية"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ تشغيل", callback_data="start_bot"),
            InlineKeyboardButton("⏹️ إيقاف", callback_data="stop_bot"),
        ],
        [InlineKeyboardButton("🔍 تحليل عملة", callback_data="analyze")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_start_message_text() -> str:
    """إنشاء نص رسالة البداية"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "يعمل" if bot_state["is_active"] else "متوقف"

    text = (
        "💎 **THE BEST BOT** 💎\n"
        f"*{current_time}*\n\n"
        f"**حالة البوت:** {status}\n\n"
        "--- *الشروط* ---\n"
        "هذا البوت مخصص للتحليل الفني فقط ولا يعتبر نصيحة استثمارية. "
        "استخدم المعلومات على مسؤوليتك الخاصة."
    )
    return text

# --- معالجات الأوامر والأزرار ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج أمر /start"""
    user = update.effective_user
    logger.info(f"User {user.first_name} started the bot.")

    await update.message.reply_html(
        f"أهلاً بك يا {user.mention_html()}!",
        quote=False
    )
    await update.message.reply_text(
        get_start_message_text(),
        reply_markup=get_keyboard(),
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """معالج ضغطات الأزرار"""
    query = update.callback_query
    await query.answer()  # ضروري لإعلام تليجرام بأن الضغطة تمت معالجتها

    callback_data = query.data
    logger.info(f"Button pressed: {callback_data}")

    if callback_data == "start_bot":
        bot_state["is_active"] = True
        await query.edit_message_text(
            text=get_start_message_text(),
            reply_markup=get_keyboard(),
            parse_mode='Markdown'
        )
    elif callback_data == "stop_bot":
        bot_state["is_active"] = False
        await query.edit_message_text(
            text=get_start_message_text(),
            reply_markup=get_keyboard(),
            parse_mode='Markdown'
        )
    elif callback_data == "analyze":
        if not bot_state["is_active"]:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.")
            return

        # في المرحلة التالية، سيتم عرض قائمة العملات هنا
        await context.bot.send_message(chat_id=update.effective_chat.id, text="ميزة التحليل قيد التطوير وسيتم إضافتها في المرحلة التالية.")

# --- الدالة الرئيسية لتشغيل البوت ---

def main() -> None:
    """دالة التشغيل الرئيسية للبوت"""
    config = get_config()
    token = config['telegram']['BOT_TOKEN']

    if not token:
        logger.error("خطأ: لم يتم العثور على رمز بوت التليجرام في ملف .env. يرجى إضافته.")
        return

    # إنشاء التطبيق
    application = Application.builder().token(token).build()

    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot is starting...")
    # تشغيل البوت
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
