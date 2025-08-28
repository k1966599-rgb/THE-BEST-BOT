import datetime
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application
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

async def show_symbol_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays a menu to select a symbol for analysis.
    """
    # These could be dynamically fetched from config or a user's list
    popular_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]

    keyboard = []
    # Create a 2-column layout for the buttons
    for i in range(0, len(popular_symbols), 2):
        row = [
            InlineKeyboardButton(popular_symbols[i], callback_data=f'select_symbol_{popular_symbols[i]}'),
        ]
        if i + 1 < len(popular_symbols):
             row.append(InlineKeyboardButton(popular_symbols[i+1], callback_data=f'select_symbol_{popular_symbols[i+1]}'))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "اختر العملة للتحليل:"
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup)


async def show_timeframe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
    """
    Displays the wave analysis submenu with timeframe options for the selected symbol.
    """
    keyboard = [
        [InlineKeyboardButton("بحث عن صفقة طويلة المدى (4h)", callback_data=f'run_strategy_h4_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (15m)", callback_data=f'run_strategy_m15_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (5m)", callback_data=f'run_strategy_m5_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (3m)", callback_data=f'run_strategy_m3_{symbol}')],
        [InlineKeyboardButton("رجوع (اختيار العملة) ⬅️", callback_data='wave_analysis_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"اختر الإطار الزمني لتحليل **{symbol}**:"
    await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')


async def _handle_strategy_analysis(strategy_func, symbol: str, interval_str: str) -> str:
    """
    Runs a strategy analysis for a given symbol and formats the response text.
    """
    scenarios, data_with_indicators = await asyncio.to_thread(strategy_func, symbol)

    if not scenarios:
        return f"لم يتم العثور على أي أنماط موجية لـ **{symbol}** حالياً على فريم {interval_str}."

    # Always generate the main analysis report
    wave_report = format_elliott_wave_report(symbol, interval_str, scenarios)

    # Propose a trade based on the scenarios
    trade_signal = propose_trade(scenarios, interval_str, data_with_indicators)

    # If a trade is proposed (or an analysis-only signal), format it
    if trade_signal:
        trade_alert = format_trade_alert(trade_signal, interval_str, symbol, scenarios)
        return f"{wave_report}\n\n{trade_alert}"
    # Otherwise, just return the wave report with a "no trade" message
    else:
        return f"{wave_report}\n\n*لا توجد فرصة تداول واضحة بناءً على الأنماط الحالية.*"


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
        await show_symbol_selection_menu(update, context)
        return

    # Handle symbol selection
    if data.startswith('select_symbol_'):
        symbol = data.split('_')[2]
        context.user_data['selected_symbol'] = symbol
        await show_timeframe_menu(update, context, symbol)
        return

    if data == 'start_bot':
        if not context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = True
            save_bot_state(True)
            # Start the background scanner task
            # We use the job queue to run it once after a short delay, ensuring the bot is ready
            context.job_queue.run_once(lambda ctx: asyncio.create_task(run_scanner(ctx.application)), 1)
            print("Scanner task scheduled.")
        await start(update, context)  # Refresh main menu
        return

    if data == 'stop_bot':
        if context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = False
            save_bot_state(False)
            # Cancel the background scanner task
            # This part is tricky as the task is not directly stored.
            # A more robust implementation would store the task future in bot_data.
            # For now, restarting the bot is the most reliable way to stop the scanner.
            print("Scanner stop requested. Please restart the bot to ensure the scanner is stopped.")
        await start(update, context)  # Refresh main menu
        return

    loading_message = "جاري تنفيذ طلبك..."
    await query.edit_message_text(text=loading_message)
    response_text = ""
    reply_markup = [[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]

    # Handle dynamic strategy execution
    if data.startswith('run_strategy_'):
        try:
            parts = data.split('_')
            strategy_key = parts[2]
            symbol = parts[3]

            strategy_map = {
                'h4': (h4_long_term_strategy, "4h"),
                'm15': (m15_scalp_strategy, "15m"),
                'm5': (m5_scalp_strategy, "5m"),
                'm3': (m3_scalp_strategy, "3m"),
            }

            if strategy_key in strategy_map:
                strategy_func, interval_str = strategy_map[strategy_key]
                # Note: The _handle_strategy_analysis function now handles the tuple return
                response_text = await _handle_strategy_analysis(strategy_func, symbol, interval_str)
            else:
                response_text = "استراتيجية غير معروفة."

        except IndexError:
            response_text = "خطأ في تحليل أمر الاستراتيجية. يرجى المحاولة مرة أخرى."

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

# --- State Persistence ---
STATE_FILE = ".bot_state.json"

def save_bot_state(is_running: bool):
    """Saves the running state of the bot to a file."""
    with open(STATE_FILE, "w") as f:
        json.dump({"is_running": is_running}, f)
    print(f"Bot state saved: is_running={is_running}")

def load_bot_state() -> bool:
    """Loads the running state of the bot from a file."""
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            is_running = state.get("is_running", False)
            print(f"Bot state loaded: is_running={is_running}")
            return is_running
    except (FileNotFoundError, json.JSONDecodeError):
        print("No valid state file found. Defaulting to not running.")
        return False
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
        await show_symbol_selection_menu(update, context)
        return

    # Handle symbol selection
    if data.startswith('select_symbol_'):
        symbol = data.split('_')[2]
        context.user_data['selected_symbol'] = symbol
        await show_timeframe_menu(update, context, symbol)
        return

    if data == 'start_bot':
        if not context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = True
            save_bot_state(True)
            # Start the background scanner task
            scanner_task = asyncio.create_task(run_scanner(context.application))
            context.bot_data['scanner_task'] = scanner_task
            print("Scanner task created.")
        await start(update, context)  # Refresh main menu
        return

    if data == 'stop_bot':
        if context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = False
            save_bot_state(False)
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

    # Handle dynamic strategy execution
    if data.startswith('run_strategy_'):
        try:
            parts = data.split('_')
            strategy_key = parts[2]
            symbol = parts[3]

            strategy_map = {
                'h4': (h4_long_term_strategy, "4h"),
                'm15': (m15_scalp_strategy, "15m"),
                'm5': (m5_scalp_strategy, "5m"),
                'm3': (m3_scalp_strategy, "3m"),
            }

            if strategy_key in strategy_map:
                strategy_func, interval_str = strategy_map[strategy_key]
                # Note: The _handle_strategy_analysis function now handles the tuple return
                response_text = await _handle_strategy_analysis(strategy_func, symbol, interval_str)
            else:
                response_text = "استراتيجية غير معروفة."

        except IndexError:
            response_text = "خطأ في تحليل أمر الاستراتيجية. يرجى المحاولة مرة أخرى."

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

# --- State Persistence ---
STATE_FILE = ".bot_state.json"

def save_bot_state(is_running: bool):
    """Saves the running state of the bot to a file."""
    with open(STATE_FILE, "w") as f:
        json.dump({"is_running": is_running}, f)
    print(f"Bot state saved: is_running={is_running}")

def load_bot_state() -> bool:
    """Loads the running state of the bot from a file."""
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            is_running = state.get("is_running", False)
            print(f"Bot state loaded: is_running={is_running}")
            return is_running
    except (FileNotFoundError, json.JSONDecodeError):
        print("No valid state file found. Defaulting to not running.")
        return False
