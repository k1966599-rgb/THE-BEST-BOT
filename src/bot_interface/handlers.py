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
from src.bot_interface.formatters import format_elliott_wave_report, format_trade_alert

BOT_NAME = "Elliott Wave Bot"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays the main menu.
    """
    if 'user_id' not in context.bot_data:
        context.bot_data['user_id'] = update.effective_chat.id
        print(f"User ID {update.effective_chat.id} stored.")

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
        await update.callback_query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=text, reply_markup=reply_markup, parse_mode='Markdown'
        )

async def show_symbol_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Displays a menu to select a symbol for analysis.
    """
    popular_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    keyboard = []
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
    Runs a strategy analysis for a given symbol in a non-blocking way
    and formats the response text.
    """
    # Run the blocking strategy function in a separate thread
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

    if 'is_running' not in context.bot_data:
        context.bot_data['is_running'] = False

    if data == 'main_menu':
        await start(update, context)
        return

    if data == 'wave_analysis_menu':
        await show_symbol_selection_menu(update, context)
        return

    if data.startswith('select_symbol_'):
        symbol = data.split('_')[2]
        context.user_data['selected_symbol'] = symbol
        await show_timeframe_menu(update, context, symbol)
        return

    if data == 'start_bot':
        if not context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = True
            save_bot_state(True)
            # This logic is now handled in bot.py's main startup sequence
            print("Scanner start requested. It will begin on the next cycle if not already running.")
        await start(update, context)
        return

    if data == 'stop_bot':
        if context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = False
            save_bot_state(False)
            print("Scanner stop requested. Please restart the bot to stop the scanner.")
        await start(update, context)
        return

    loading_message = "جاري تنفيذ طلبك..."
    await query.edit_message_text(text=loading_message)
    response_text = ""
    reply_markup = [[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]

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
                response_text = await _handle_strategy_analysis(strategy_func, symbol, interval_str)
            else:
                response_text = "استراتيجية غير معروفة."

        except IndexError:
            response_text = "خطأ في تحليل أمر الاستراتيجية. يرجى المحاولة مرة أخرى."

    elif data == 'active_trades':
        response_text = "📈 **الصفقات النشطة**\n\n(هذه الميزة قيد التطوير)"
    elif data == 'statistics':
        response_text = "📋 **الاحصائيات**\n\n(هذه الميزة قيد التطوير)"
    else:
        response_text = "أمر غير معروف."

    try:
        await query.edit_message_text(
            text=response_text,
            reply_markup=InlineKeyboardMarkup(reply_markup),
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"An error occurred while editing message: {e}")

# --- State Persistence ---
STATE_FILE = ".bot_state.json"

def save_bot_state(is_running: bool):
    with open(STATE_FILE, "w") as f:
        json.dump({"is_running": is_running}, f)
    print(f"Bot state saved: is_running={is_running}")

def load_bot_state() -> bool:
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
            is_running = state.get("is_running", False)
            print(f"Bot state loaded: is_running={is_running}")
            return is_running
    except (FileNotFoundError, json.JSONDecodeError):
        print("No valid state file found. Defaulting to not running.")
        return False
