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

# Bot state
bot_state = {"is_active": True}

# --- Keyboard & Message Generators ---

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
        # Create a row of 2 buttons for each coin
        [InlineKeyboardButton(coin, callback_data=f"coin_{coin}") for coin in WATCHLIST[i:i+2]]
        for i in range(0, len(WATCHLIST), 2)
    ]
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="start_menu")])
    return InlineKeyboardMarkup(keyboard)

def get_start_message_text() -> str:
    """Creates the elaborate start message text."""
    config = get_config()
    status = "🟢 متصل وجاهز للعمل" if bot_state["is_active"] else "🔴 متوقف"
    platform = config['trading'].get('EXCHANGE_ID', 'N/A').upper()
    text = (
        f"╔═══════════════════════════════════════╗\n"
        f"║            💎 THE BEST BOT 💎           ║\n"
        f"╚═══════════════════════════════════════╝\n\n"
        f"🕐 **التوقيت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"📶 **حالة النظام:** {status}\n"
        f"🌐 **المنصة:** 🏛️ {platform} Exchange\n\n"
        f"📱 استخدم الأزرار أدناه للتفاعل مع النظام 👇"
    )
    return text

# --- Command & Callback Handlers ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for the /start command."""
    await update.message.reply_text(
        text=get_start_message_text(),
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def main_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for all button presses."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "start_menu":
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='Markdown')

    elif callback_data == "start_bot":
        bot_state["is_active"] = True
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='Markdown')

    elif callback_data == "stop_bot":
        bot_state["is_active"] = False
        await query.edit_message_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='Markdown')

    elif callback_data == "analyze_menu":
        if not bot_state["is_active"]:
            await query.message.reply_text("البوت متوقف حاليًا. يرجى الضغط على 'تشغيل' أولاً.")
            return
        await query.edit_message_text(text="الرجاء اختيار عملة للتحليل:", reply_markup=get_coin_list_keyboard())

    elif callback_data.startswith("coin_"):
        symbol = callback_data.split("_")[1]
        await query.edit_message_text(text=f"جاري تحليل {symbol}، قد يستغرق هذا بعض الوقت...")

        try:
            config = get_config()
            # Run the analysis engine from run_bot.py
            final_report = get_ranked_analysis_for_symbol(symbol, config)
            # The sender function will handle splitting long messages
            send_telegram_message(final_report)
            # After sending the report, show the main menu again
            await query.message.reply_text(text=get_start_message_text(), reply_markup=get_main_keyboard(), parse_mode='Markdown')
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
