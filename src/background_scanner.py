import asyncio
import datetime
import traceback
from telegram.ext import Application
from typing import Dict, Any, List

from src.utils.config_loader import config
from src.bot_interface.formatters import format_trade_alert
from src.analysis_manager import AnalysisManager

SCAN_INTERVAL_SECONDS = config.get('scanner', {}).get('interval_seconds', 900)

def analyze_symbol_sync(symbol: str, last_alerted: Dict[str, Any]) -> list:
    """
    Uses the AnalysisManager to perform a full hierarchical analysis for a single symbol.
    Returns a list of alerts to be sent.
    """
    alerts_to_send = []
    manager = AnalysisManager(symbol)
    manager.run_hierarchical_analysis()

    decision = manager.context.get("final_decision")
    trade_setup = manager.context.get("final_trade_setup")

    # Define a unique key for the potential trade to avoid spamming alerts
    # Using the pattern type and the start/end prices is a good way to identify a setup
    if trade_setup:
        reason = trade_setup.get('reason', '')
        alert_key = f"{symbol}-{trade_setup.get('pattern_type')}-{reason}"
    else:
        # If no trade setup, no alert can be generated
        return []

    # Case 1: A trade is fully confirmed and ready to be sent
    if decision == "ACCEPT":
        if last_alerted.get(alert_key) != "ACCEPTED":
            scenarios = manager.context.get("15m_scenarios", [])
            alert_text = format_trade_alert(trade_setup, "15m", symbol, scenarios)
            # Higher priority for accepted trades
            alerts_to_send.append((alert_text, 'trade', 1))
            last_alerted[alert_key] = "ACCEPTED"

    # Case 2: A valid setup was found, but it's not ready yet (e.g., price not in zone)
    elif decision == "DEFER":
        if last_alerted.get(alert_key) is None:
            # This is a high-quality "potential opportunity"
            info_text = (f"⏳ **فرصة محتملة للمراقبة | {symbol}**\n"
                         f"**النمط:** `{trade_setup.get('pattern_type')}`\n"
                         f"**السبب:** {trade_setup.get('reason')}\n"
                         f"**الحالة:** {manager.context['decision_path'][-1]}") # Get the last reason for deferral

            # Lower priority for deferred trades
            alerts_to_send.append((info_text, 'info', 10))
            last_alerted[alert_key] = "DEFERRED"

    return alerts_to_send


async def run_scanner(app: Application):
    """
    The main background task that runs the analysis for all symbols,
    collects all alerts, sorts them, and sends a single consolidated message.
    """
    print("Background scanner started.")
    last_alerted_setups: Dict[str, str] = {}
    symbols_to_scan = config['symbols_to_scan']
    print(f"Scanner will analyze the following symbols: {symbols_to_scan}")

    while True:
        try:
            print(f"[{datetime.datetime.now()}] Running new automatic scan cycle...")
            user_id = app.bot_data.get('user_id')
            if not user_id:
                print("User ID not found in bot_data, skipping scan cycle.")
                await asyncio.sleep(10)
                continue

            all_alerts_for_cycle = []
            for symbol in symbols_to_scan:
                alerts = await asyncio.to_thread(
                    analyze_symbol_sync, symbol, last_alerted_setups
                )
                if alerts:
                    all_alerts_for_cycle.extend(alerts)

            if all_alerts_for_cycle:
                all_alerts_for_cycle.sort(key=lambda x: x[2])

                trade_alerts = [a[0] for a in all_alerts_for_cycle if a[1] == 'trade']
                info_alerts = [a[0] for a in all_alerts_for_cycle if a[1] == 'info']

                final_message = ""
                if trade_alerts:
                    final_message += "💎 **صفقات جاهزة (تحليل هرمي)** 💎\n\n"
                    final_message += "\n\n---\n\n".join(trade_alerts)

                if info_alerts:
                    if final_message: final_message += "\n\n"
                    final_message += "⏳ **فرص قيد المراقبة** ⏳\n\n"
                    final_message += "\n\n---\n\n".join(info_alerts)

                if final_message:
                    await app.bot.send_message(chat_id=user_id, text=final_message, parse_mode='Markdown')
            else:
                print("Scan cycle complete. No new setups found.")

            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            print("Background scanner stopped.")
            break
        except Exception as e:
            print(f"An error occurred in the main scanner loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)
