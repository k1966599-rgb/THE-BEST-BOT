import asyncio
import datetime
import traceback
from telegram.ext import Application
from typing import Dict, Any, List, Tuple

from src.utils.config_loader import config
from src.data.bybit_client import BybitClient
from src.analysis.support_resistance import find_supply_demand_zones
from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import define_trade_setup
from src.bot_interface.formatters import format_trade_alert

LOWER_TIMEFRAME_STRATEGIES = [
    (m15_scalp_strategy, "15m"),
    (m5_scalp_strategy, "5m"),
    (m3_scalp_strategy, "3m"),
]

SCAN_INTERVAL_SECONDS = 900

def analyze_symbol_sync(symbol: str, client: BybitClient, last_alerted_pattern_time: Dict[str, Any]) -> list:
    """
    Analyzes a single symbol and returns a list of alerts with priority.
    Alert format: (alert_text, alert_type, priority)
    Priority: Lower is better. Trades are prioritized by price proximity. Info alerts have low priority.
    """
    alerts_to_send = []
    print(f"--- Analyzing {symbol} ---")

    htf_data = client.get_historical_data(symbol, "240")
    if htf_data is None or htf_data.empty:
        print(f"  - Could not fetch HTF data for {symbol}. Skipping.")
        return alerts_to_send

    htf_zones = find_supply_demand_zones(htf_data)
    current_price = htf_data['close'].iloc[-1]

    is_near_htf_demand = any(
        zone['type'] == 'demand' and (zone['bottom'] * 0.995 < current_price < zone['top'] * 1.005)
        for zone in htf_zones
    )
    if not is_near_htf_demand:
        return alerts_to_send

    print(f"  - Price near HTF demand. Scanning lower timeframes for entry patterns...")
    for strategy_func, timeframe in LOWER_TIMEFRAME_STRATEGIES:
        try:
            scenarios, data_with_indicators = strategy_func(symbol, strict=True)
            if not scenarios or data_with_indicators is None or data_with_indicators.empty:
                continue

            latest_primary_pattern = scenarios[0].primary_pattern
            latest_pattern_timestamp = latest_primary_pattern.points[-1].time
            alert_key = f"{symbol}-{timeframe}"

            if last_alerted_pattern_time.get(alert_key) != latest_pattern_timestamp:
                info_alert_text = f"⚠️ **فرصة محتملة | {symbol} | {timeframe}**\nنمط `{latest_primary_pattern.pattern_type}` عند منطقة طلب 4 ساعات."
                alerts_to_send.append((info_alert_text, 'info', 999))
                last_alerted_pattern_time[alert_key] = latest_pattern_timestamp

                trade_setup = define_trade_setup(scenarios, data_with_indicators)

                if trade_setup:
                    current_price_ltf = data_with_indicators['close'].iloc[-1]
                    entry_zone = trade_setup['entry_zone']
                    is_in_zone = entry_zone[1] <= current_price_ltf <= entry_zone[0]

                    if is_in_zone:
                        print(f"  - {symbol}/{timeframe}: Price {current_price_ltf:.2f} is in the Fib entry zone.")
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
                            print(f"  - {symbol}/{timeframe}: CONFIRMED! Stoch, MACD, and Volume are bullish.")
                            alert_text = format_trade_alert(trade_setup, timeframe, symbol, scenarios)
                            priority = abs(current_price_ltf - trade_setup['entry']) / current_price_ltf  # Normalized proximity
                            alerts_to_send.append((alert_text, 'trade', priority))
                        else:
                            print(f"  - {symbol}/{timeframe}: In zone, but waiting for indicator confirmation.")
        except Exception as e:
            print(f"    - CRITICAL ERROR during LTF scan on {symbol}/{timeframe}: {e}")
            traceback.print_exc()

    return alerts_to_send


async def run_scanner(app: Application):
    """
    The main background task that runs the analysis for all symbols,
    collects all alerts, sorts them, and sends a single consolidated message.
    """
    print("Background scanner started.")
    last_alerted_pattern_time = {}
    client = BybitClient()
    symbols_to_scan = config['symbols_to_scan']
    print(f"Scanner will analyze the following symbols: {symbols_to_scan}")

    while True:
        try:
            print(f"[{datetime.datetime.now()}] Running new automatic scan cycle...")
            user_id = app.bot_data.get('user_id')
            if not user_id:
                await asyncio.sleep(5)
                continue

            all_alerts_for_cycle = []
            for symbol in symbols_to_scan:
                alerts = await asyncio.to_thread(
                    analyze_symbol_sync, symbol, client, last_alerted_pattern_time
                )
                if alerts:
                    all_alerts_for_cycle.extend(alerts)

            if all_alerts_for_cycle:
                # Sort alerts by priority (lower is better)
                all_alerts_for_cycle.sort(key=lambda x: x[2])

                # Separate into ready trades and potential opportunities
                trade_alerts = [a[0] for a in all_alerts_for_cycle if a[1] == 'trade']
                info_alerts = [a[0] for a in all_alerts_for_cycle if a[1] == 'info']

                # Build the consolidated message
                final_message = ""
                if trade_alerts:
                    final_message += "💎 **صفقات جاهزة للتنفيذ** 💎\n"
                    final_message += "\n\n---\n\n".join(trade_alerts)
                    final_message += "\n\n"

                if info_alerts:
                    final_message += "⏳ **فرص محتملة للمراقبة** ⏳\n"
                    final_message += "\n\n---\n\n".join(info_alerts)

                if final_message:
                    await app.bot.send_message(chat_id=user_id, text=final_message, parse_mode='Markdown')
            else:
                # Only send the "no opportunities" message if no alerts of any kind were found
                await app.bot.send_message(chat_id=user_id, text="✅ اكتمل الفحص. لا توجد فرص جديدة.", disable_notification=True)

            print("Scan cycle complete.")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            print("Background scanner stopped.")
            break
        except Exception as e:
            print(f"An error occurred in the main scanner loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)
