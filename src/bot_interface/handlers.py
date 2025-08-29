import datetime
import asyncio
import json
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import pandas as pd
import os
from telegram.ext import ContextTypes, Application, ConversationHandler, MessageHandler, filters

from src.background_scanner import run_scanner
from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import define_trade_setup
from src.bot_interface.formatters import format_elliott_wave_report, format_trade_alert
from src.trading import state_manager, trade_logger
from src.utils.config_loader import load_config
from src.utils import config_manager

BOT_NAME = "Elliott Wave Bot"

# --- Conversation States ---
AWAITING_SYMBOL_TO_ADD = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the main menu."""
    if 'user_id' not in context.bot_data:
        context.bot_data['user_id'] = update.effective_chat.id
    is_running = context.bot_data.get('is_running', False)
    status_text = "الحالة: 🟢 يعمل" if is_running else "الحالة: 🔴 متوقف"
    keyboard = [
        [InlineKeyboardButton("🟢 تشغيل البوت", callback_data='start_bot'), InlineKeyboardButton("🔴 ايقاف البوت", callback_data='stop_bot')],
        [InlineKeyboardButton("📊 تحليل موجي", callback_data='wave_analysis_menu')],
        [InlineKeyboardButton("📈 الصفقات النشطة", callback_data='active_trades'), InlineKeyboardButton("📋 الاحصائيات", callback_data='statistics')],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data='settings_menu')]
    ]
    text = f"**{BOT_NAME}**\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{status_text}\n\nاختر احد الأوامر:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, status_message: str = None) -> None:
    """Displays the main settings menu, showing current symbols and management options."""
    query = update.callback_query
    if query:
        await query.answer()

    config = load_config()
    symbols_list = config.get('symbols_to_scan', [])

    if symbols_list:
        symbols_text = "\n".join([f"- `{symbol}`" for symbol in symbols_list])
    else:
        symbols_text = "لا توجد عملات في قائمة المراقبة حاليًا."

    header_text = f"⚙️ **إعدادات البوت** ⚙️"
    if status_message:
        # Prepend status message if it exists
        header_text = f"{status_message}\n\n{header_text}"

    text = f"{header_text}\n\n" \
           f"**العملات قيد المراقبة حاليًا:**\n{symbols_text}\n\n" \
           f"اختر الإجراء الذي تريد القيام به:"

    keyboard = [
        [InlineKeyboardButton("➕ إضافة عملة", callback_data='add_symbol_start')],
        [InlineKeyboardButton("➖ حذف عملة", callback_data='remove_symbol_start')],
        [InlineKeyboardButton("⬅️ رجوع إلى القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode='Markdown')


async def add_symbol_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new symbol."""
    query = update.callback_query
    await query.answer()
    # Store the message ID so we can edit it later after the user replies.
    context.user_data['settings_message_id'] = query.message.message_id
    text = "يرجى إرسال رمز العملة التي تريد إضافتها (مثال: `BTCUSDT`).\n\nلإلغاء العملية، اكتب /cancel."
    await query.edit_message_text(text=text, parse_mode='Markdown')
    return AWAITING_SYMBOL_TO_ADD


async def add_symbol_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the symbol, adds it to the config, and shows the updated settings menu."""
    message_id = context.user_data.get('settings_message_id')
    chat_id = update.effective_chat.id
    new_symbol = update.message.text.upper().strip()

    # Delete the user's message to keep the chat clean
    await update.message.delete()

    if not new_symbol.endswith("USDT") or " " in new_symbol or len(new_symbol) > 20:
        await context.bot.send_message(chat_id=chat_id, text="رمز العملة غير صالح. يرجى المحاولة مرة أخرى أو اكتب /cancel للإلغاء.")
        # We stay in the same state, waiting for a valid symbol
        return AWAITING_SYMBOL_TO_ADD

    was_added = config_manager.add_symbol_to_config(new_symbol)

    # Re-generate the settings menu text to show the result
    config = load_config()
    symbols_list = config.get('symbols_to_scan', [])
    symbols_text = "\n".join([f"- `{symbol}`" for symbol in symbols_list]) if symbols_list else "لا توجد عملات."

    if was_added:
        status_text = f"✅ تم إضافة `{new_symbol}` بنجاح."
    else:
        status_text = f"⚠️ العملة `{new_symbol}` موجودة بالفعل في القائمة."

    text = f"⚙️ **إعدادات البوت** ⚙️\n\n{status_text}\n\n" \
           f"**العملات قيد المراقبة حاليًا:**\n{symbols_text}\n\n" \
           f"اختر الإجراء الذي تريد القيام به:"

    keyboard = [
        [InlineKeyboardButton("➕ إضافة عملة", callback_data='add_symbol_start')],
        [InlineKeyboardButton("➖ حذف عملة", callback_data='remove_symbol_start')],
        [InlineKeyboardButton("⬅️ رجوع إلى القائمة الرئيسية", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Edit the original message with the updated menu
    if message_id:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception as e:
            print(f"Error editing message: {e}") # Handle case where message is too old
            # If editing fails, send a new message
            await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')

    # Clean up and end conversation
    if 'settings_message_id' in context.user_data:
        del context.user_data['settings_message_id']
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation, cleaning up user_data."""
    await update.message.reply_text('تم إلغاء العملية. اضغط /start للعودة إلى القائمة الرئيسية.')
    if 'settings_message_id' in context.user_data:
        del context.user_data['settings_message_id']
    return ConversationHandler.END


async def remove_symbol_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a menu with all current symbols, allowing the user to select one for removal."""
    query = update.callback_query
    await query.answer()

    symbols_list = config_manager.get_symbols_from_config()

    if not symbols_list:
        await query.edit_message_text(text="لا توجد عملات لحذفها.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data='settings_menu')]]))
        return

    keyboard = []
    # Create a button for each symbol, two per row
    for i in range(0, len(symbols_list), 2):
        row = [
            InlineKeyboardButton(f"❌ {symbols_list[i]}", callback_data=f"remove_symbol_confirm_{symbols_list[i]}")
        ]
        if i + 1 < len(symbols_list):
            row.append(InlineKeyboardButton(f"❌ {symbols_list[i+1]}", callback_data=f"remove_symbol_confirm_{symbols_list[i+1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data='settings_menu')])

    text = "اختر العملة التي تريد حذفها من قائمة المراقبة:"
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_symbol_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a menu to select a symbol for analysis."""
    popular_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    keyboard = [[InlineKeyboardButton(s, callback_data=f'select_symbol_{s}') for s in popular_symbols[i:i+2]] for i in range(0, len(popular_symbols), 2)]
    keyboard.append([InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')])
    await update.callback_query.edit_message_text(text="اختر العملة للتحليل:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_timeframe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
    """Displays the timeframe options for the selected symbol."""
    keyboard = [
        [InlineKeyboardButton("بحث عن صفقة طويلة المدى (4h)", callback_data=f'run_strategy_h4_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (15m)", callback_data=f'run_strategy_m15_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (5m)", callback_data=f'run_strategy_m5_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (3m)", callback_data=f'run_strategy_m3_{symbol}')],
        [InlineKeyboardButton("رجوع (اختيار العملة) ⬅️", callback_data='wave_analysis_menu')]
    ]
    await update.callback_query.edit_message_text(text=f"اختر الإطار الزمني لتحليل **{symbol}**:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def _run_strategy_sync(strategy_func, symbol):
    """Synchronous wrapper for the blocking strategy call."""
    return strategy_func(symbol)

async def _create_and_send_analysis_report(update: Update, context: ContextTypes.DEFAULT_TYPE, strategy_func, symbol: str, interval_str: str):
    """
    Runs the heavy analysis in a separate thread and sends the results when complete.
    """
    try:
        scenarios, data_with_indicators = await asyncio.to_thread(_run_strategy_sync, strategy_func, symbol)

        if not scenarios:
            response_text = f"لم يتم العثور على أي أنماط موجية لـ **{symbol}** حالياً على فريم {interval_str}."
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text, parse_mode='Markdown')
            return

        wave_report = format_elliott_wave_report(symbol, interval_str, scenarios)
        trade_setup = define_trade_setup(scenarios, data_with_indicators)

        # If no trade setup is found, or if it's just 'Analysis', show the basic report.
        if not trade_setup or trade_setup.get('type') != 'LONG':
            reason = "*لا توجد فرصة تداول واضحة بناءً على الأنماط الحالية.*"
            if trade_setup and trade_setup.get('reason'):
                reason = f"*{trade_setup.get('reason')}*"
            response_text = f"{wave_report}\n\n{reason}"
            await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text, parse_mode='Markdown')
            return

        # If we have a valid LONG trade setup, check its status
        current_price_ltf = data_with_indicators['close'].iloc[-1]
        entry_zone = trade_setup['entry_zone']
        is_in_zone = entry_zone[1] <= current_price_ltf <= entry_zone[0]
        trade_alert = format_trade_alert(trade_setup, interval_str, symbol, scenarios)

        if is_in_zone:
            latest_indicators = data_with_indicators.iloc[-1]
            stoch_k = latest_indicators.get('STOCHRSIk_14_14_3_3', 50)
            stoch_d = latest_indicators.get('STOCHRSId_14_14_3_3', 50)
            macd_hist = latest_indicators.get('MACDh_12_26_9', 0)
            volume = latest_indicators.get('volume', 0)
            volume_sma = latest_indicators.get('volume_sma', 0)
            stoch_bullish = stoch_k > stoch_d and stoch_k < 60
            macd_bullish = macd_hist > 0
            volume_confirmed = volume > volume_sma * 1.2

            if stoch_bullish and macd_bullish and volume_confirmed:
                response_text = f"{wave_report}\n\n{trade_alert}"
            else:
                response_text = f"{wave_report}\n\n{trade_alert}\n\n**الحالة:** السعر في منطقة الدخول، ولكننا ننتظر تأكيدًا أقوى من المؤشرات."
        else:
            response_text = f"{wave_report}\n\n{trade_alert}\n\n**الحالة:** تم تحديد فرصة محتملة، ننتظر وصول السعر إلى منطقة الدخول."

        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text, parse_mode='Markdown')

    except Exception as e:
        print(f"--- FATAL ERROR IN HANDLER ---")
        traceback.print_exc()
        response_text = f"حدث خطأ فادح أثناء تحليل {symbol}. يرجى مراجعة السجل."
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text, parse_mode='Markdown')


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- Menu Navigation ---
    if data == 'main_menu':
        await start(update, context)
        return
    if data == 'wave_analysis_menu':
        await show_symbol_selection_menu(update, context)
        return
    if data.startswith('select_symbol_'):
        symbol = data.split('_')[2]
        await show_timeframe_menu(update, context, symbol)
        return

    # --- Bot State Control ---
    if data == 'start_bot':
        if not context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = True
            save_bot_state(True)
            print("Scanner start requested. It will begin on the next bot restart or cycle.")
        await start(update, context)
        return
    if data == 'stop_bot':
        if context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = False
            save_bot_state(False)
            print("Scanner stop requested. Please restart the bot to ensure the scanner is stopped.")
        await start(update, context)
        return

    # --- Strategy Execution ---
    if data.startswith('run_strategy_'):
        try:
            parts = data.split('_')
            strategy_key, symbol = parts[2], parts[3]
            strategy_map = {'h4': (h4_long_term_strategy, "4h"), 'm15': (m15_scalp_strategy, "15m"), 'm5': (m5_scalp_strategy, "5m"), 'm3': (m3_scalp_strategy, "3m")}

            if strategy_key in strategy_map:
                strategy_func, interval_str = strategy_map[strategy_key]
                # Acknowledge immediately
                await query.edit_message_text(text=f"طلبك لتحليل {symbol} على فريم {interval_str} قيد المعالجة... سأرسل النتائج في رسالة جديدة عند اكتمالها.")
                # Schedule the heavy lifting to run in the background
                asyncio.create_task(_create_and_send_analysis_report(update, context, strategy_func, symbol, interval_str))
            else:
                await query.edit_message_text(text="استراتيجية غير معروفة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))
        except IndexError:
            await query.edit_message_text(text="خطأ في تحليل أمر الاستراتيجية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))
        return

    # --- Settings Menu ---
    if data == 'settings_menu':
        await show_settings_menu(update, context)
        return
    if data == 'remove_symbol_start':
        await remove_symbol_menu(update, context)
        return
    if data.startswith('remove_symbol_confirm_'):
        symbol_to_remove = data.split('_')[-1]
        was_removed = config_manager.remove_symbol_from_config(symbol_to_remove)

        status_message = f"✅ تم حذف `{symbol_to_remove}` بنجاح." if was_removed else f"⚠️ لم يتم العثور على `{symbol_to_remove}`."
        await show_settings_menu(update, context, status_message=status_message)
        return

    # --- Active Trades / Stats ---
    if data == 'active_trades':
        active_trades = state_manager.load_active_trades()
        if not active_trades:
            text = "📈 **الصفقات النشطة**\n\nلا توجد صفقات نشطة حاليًا."
        else:
            text = f"📈 **الصفقات النشطة ({len(active_trades)})**\n\n"
            for trade in active_trades:
                hit_targets_count = len(trade.get('hit_targets_indices', []))
                total_targets = len(trade.get('targets', []))
                text += (f"**- {trade.get('symbol')}**\n"
                         f"  - **الحالة:** {trade.get('status', 'N/A')}\n"
                         f"  - **الدخول:** ${trade.get('entry', 0):.2f}\n"
                         f"  - **الأهداف المحققة:** {hit_targets_count}/{total_targets}\n\n")

        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))
        return

    if data == 'statistics':
        text = "📋 **إحصائيات الأداء**\n\n"
        log_file = trade_logger.LOG_FILE
        if not os.path.exists(log_file):
            text += "لا يوجد سجل صفقات حتى الآن."
        else:
            try:
                df = pd.read_csv(log_file)
                if df.empty:
                     text += "لا يوجد سجل صفقات حتى الآن."
                else:
                    total_trades = len(df)
                    sl_trades = df[df['outcome'] == 'SL_HIT']
                    tp_final_trades = df[df['outcome'] == 'TP_FINAL_HIT']

                    win_rate = (len(tp_final_trades) / total_trades) * 100 if total_trades > 0 else 0
                    avg_rr = df['rr_ratio'].mean()

                    text += f"**إجمالي الصفقات المسجلة:** {total_trades}\n"
                    text += f"**صفقات رابحة (الهدف النهائي):** {len(tp_final_trades)}\n"
                    text += f"**صفقات خاسرة (وقف الخسارة):** {len(sl_trades)}\n"
                    text += f"**نسبة النجاح:** {win_rate:.1f}%\n"
                    text += f"**متوسط R:R:** {avg_rr:.2f}\n"

            except Exception as e:
                text += f"حدث خطأ أثناء قراءة سجل الصفقات: {e}"

        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))
        return

# --- State Persistence ---
STATE_FILE = ".bot_state.json"
def save_bot_state(is_running: bool):
    with open(STATE_FILE, "w") as f: json.dump({"is_running": is_running}, f)
def load_bot_state() -> bool:
    try:
        with open(STATE_FILE, "r") as f: return json.load(f).get("is_running", False)
    except (FileNotFoundError, json.JSONDecodeError): return False
