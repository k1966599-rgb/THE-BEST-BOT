import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.background_scanner import run_scanner

from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import propose_trade
from src.bot_interface.formatters import format_elliott_wave_report

BOT_NAME = "Elliott Wave Bot"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays the main menu.
    """
    # Store user_id for background tasks
    if 'user_id' not in context.bot_data:
        context.bot_data['user_id'] = update.effective_chat.id
        print(f"User ID {update.effective_chat.id} stored.")

    # Safely get the running state, default to False if not set
    is_running = context.bot_data.get('is_running', False)
    status_text = "الحالة: 🟢 يعمل" if is_running else "الحالة: 🔴 متوقف"

    keyboard = [
        [
            InlineKeyboardButton("🟢 تشغيل البوت", callback_data='start_bot'),
            InlineKeyboardButton("🔴 ايقاف البوت", callback_data='stop_bot')
        ],
        [InlineKeyboardButton("📊 تحليل موجي", callback_data='wave_analysis_menu')],
        [InlineKeyboardButton("📈 الصفقات النشطة", callback_data='active_trades')],
        [InlineKeyboardButton("📋 الاحصائيات", callback_data='statistics')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"**{BOT_NAME}**\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{status_text}\n\n"
    text += "اختر احد الأوامر:"

    if update.callback_query:
        # Edit the message to show the new menu
        await update.callback_query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode='Markdown'
        )
    else:
        # Send a new message
        await update.message.reply_text(
            text=text, reply_markup=reply_markup, parse_mode='Markdown'
        )

async def wave_analysis_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays the wave analysis submenu with timeframe options.
    """
    keyboard = [
        [InlineKeyboardButton("بحث عن صفقة طويلة المدى (4h)", callback_data='run_strategy_h4')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (15m)", callback_data='run_strategy_m15')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (5m)", callback_data='run_strategy_m5')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (3m)", callback_data='run_strategy_m3')],
        [InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "اختر الإطار الزمني للتحليل:"
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def _handle_strategy_analysis(strategy_func, interval_str: str) -> str:
    """
    Runs a strategy analysis and formats the response text.
    """
    patterns = await asyncio.to_thread(strategy_func, "BTCUSDT")

    if not patterns:
        return f"لم يتم العثور على أي أنماط موجية حالياً على فريم {interval_str}."

    # Limit the report to the top 3 most confident patterns to avoid message length errors
    patterns_to_report = patterns[:3]

    wave_report = format_elliott_wave_report("BTCUSDT", interval_str, patterns_to_report)
    trade_signal = propose_trade(patterns, interval_str)

    if not trade_signal:
        return wave_report + "\n\n*لا توجد فرصة تداول واضحة بناءً على الأنماط الحالية.*"

    entry_price = trade_signal['entry']
    stop_loss_price = trade_signal['stop_loss']
    sl_percentage = abs((stop_loss_price - entry_price) / entry_price) * 100

    targets_text_lines = []
    for i, target_price in enumerate(trade_signal['targets']):
        tp_percentage = abs((target_price - entry_price) / entry_price) * 100
        targets_text_lines.append(
            f"  - الهدف {i+1}: ${target_price:.2f} (+{tp_percentage:.1f}%)"
        )
    targets_text = "\n".join(targets_text_lines)

    trade_text = (
        f"\n\n**🚨 فرصة تداول مقترحة! 🚨**\n"
        f"- **السبب:** {trade_signal['reason']}\n"
        f"- **نوع الصفقة:** {trade_signal['type']}\n"
        f"- **سعر الدخول المقترح:** ${entry_price:.2f}\n"
        f"- **وقف الخسارة:** ${stop_loss_price:.2f} (-{sl_percentage:.1f}%)\n"
        f"- **الأهداف:**\n{targets_text}"
    )
    return wave_report + trade_text


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # Initialize state if it doesn't exist
    if 'is_running' not in context.bot_data:
        context.bot_data['is_running'] = False

    if data == 'main_menu':
        await start(update, context)
        return

    if data == 'wave_analysis_menu':
        await wave_analysis_menu(update, context)
        return

    if data == 'start_bot':
        if not context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = True
            # Start the background scanner task
            scanner_task = asyncio.create_task(run_scanner(context.application))
            context.bot_data['scanner_task'] = scanner_task
            print("Scanner task created.")
        await start(update, context)  # Refresh main menu
        return

    if data == 'stop_bot':
        if context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = False
            # Cancel the background scanner task
            scanner_task = context.bot_data.get('scanner_task')
            if scanner_task and not scanner_task.done():
                scanner_task.cancel()
                print("Scanner task cancelled.")
            context.bot_data['scanner_task'] = None
        await start(update, context)  # Refresh main menu
        return

    loading_message = "جاري تنفيذ طلبك..."
    await query.edit_message_text(text=loading_message)
    response_text = ""
    reply_markup = [[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]

    strategy_map = {
        'run_strategy_h4': (h4_long_term_strategy, "4h"),
        'run_strategy_m15': (m15_scalp_strategy, "15m"),
        'run_strategy_m5': (m5_scalp_strategy, "5m"),
        'run_strategy_m3': (m3_scalp_strategy, "3m"),
    }

    if data in strategy_map:
        strategy_func, interval_str = strategy_map[data]
        response_text = await _handle_strategy_analysis(strategy_func, interval_str)

    elif data == 'active_trades':
        response_text = "📈 **الصفقات النشطة**\n\n(هذه الميزة قيد التطوير)"

    elif data == 'statistics':
        response_text = "📋 **الاحصائيات**\n\n(هذه الميزة قيد التطوير)"

    elif data == 'help':
        response_text = "هذا البوت يقوم بتحليل موجات إليوت للبحث عن فرص تداول."

    else:
        response_text = "أمر غير معروف."

    try:
        await query.edit_message_text(
            text=response_text,
            reply_markup=InlineKeyboardMarkup(reply_markup),
            parse_mode='Markdown'
        )
    except Exception as e:
        if "message is too long" in str(e).lower():
            truncated_text = response_text[:4000] + "\n\n[...]\n\nالرسالة طويلة جدًا وتم اقتطاعها."
            await query.edit_message_text(
                text=truncated_text,
                reply_markup=InlineKeyboardMarkup(reply_markup),
                parse_mode='Markdown'
            )
        else:
            # Re-raise other errors
            print(f"An error occurred while editing message: {e}")
            await query.edit_message_text(
                text="حدث خطأ أثناء معالجة طلبك.",
                reply_markup=InlineKeyboardMarkup(reply_markup)
            )
