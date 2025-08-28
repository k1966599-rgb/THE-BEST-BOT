import asyncio
import datetime
import traceback
from telegram.ext import Application
from typing import Dict, Any

from src.utils.config_loader import config
from src.data.bybit_client import BybitClient
from src.analysis.support_resistance import find_supply_demand_zones
from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import propose_trade
from src.bot_interface.formatters import format_trade_alert

LOWER_TIMEFRAME_STRATEGIES = [
    (m15_scalp_strategy, "15m"),
    (m5_scalp_strategy, "5m"),
    (m3_scalp_strategy, "3m"),
]

SCAN_INTERVAL_SECONDS = 900

def analyze_symbol_sync(symbol: str, client: BybitClient, last_alerted_pattern_time: Dict[str, Any]) -> list:
    """
    This function contains the blocking (CPU-bound and I/O-bound) analysis logic
    for a single symbol. It's designed to be run in a separate thread.
    """
    alerts_to_send = []
    print(f"--- Analyzing {symbol} ---")

    # 1. Get High-Timeframe (HTF) context
    htf_data = client.get_historical_data(symbol, "240")
    if htf_data is None or htf_data.empty:
        print(f"  - Could not fetch HTF data for {symbol}. Skipping.")
        return alerts_to_send

    htf_zones = find_supply_demand_zones(htf_data)
    current_price = htf_data['close'].iloc[-1]
    print(f"  - Current price: {current_price:.2f}. Found {len(htf_zones)} HTF zones.")

    # 2. Check if price is near a HTF demand zone
    is_near_htf_demand = any(
        zone['type'] == 'demand' and (zone['bottom'] * 0.995 < current_price < zone['top'] * 1.005)
        for zone in htf_zones
    )
    if not is_near_htf_demand:
        print(f"  - Price is not near any HTF demand zone. Skipping lower timeframe analysis.")
        return alerts_to_send

    # 3. If near HTF demand, scan lower timeframes for entries
    print(f"  - Price near HTF demand. Scanning lower timeframes for entry patterns...")
    for strategy_func, timeframe in LOWER_TIMEFRAME_STRATEGIES:
        try:
            result = strategy_func(symbol, strict=False)
            loose_scenarios, _ = result if isinstance(result, tuple) and len(result) == 2 else ([], None)

            if loose_scenarios:
                latest_primary_pattern = loose_scenarios[0].primary_pattern
                latest_pattern_timestamp = latest_primary_pattern.points[-1].time
                alert_key = f"{symbol}-{timeframe}"

                if last_alerted_pattern_time.get(alert_key) != latest_pattern_timestamp:
                    alerts_to_send.append(
                        (f"⚠️ فرصة محتملة على {symbol} إطار {timeframe} (عند منطقة طلب 4 ساعات)", 'info')
                    )

                    strict_result = strategy_func(symbol, strict=True)
                    strict_scenarios, data_with_indicators = strict_result if isinstance(strict_result, tuple) and len(strict_result) == 2 else ([], None)

                    if strict_scenarios and data_with_indicators is not None:
                        trade_signal = propose_trade(strict_scenarios, timeframe, data_with_indicators)
                        if trade_signal:
                            alert_text = format_trade_alert(trade_signal, timeframe, symbol, strict_scenarios)
                            alerts_to_send.append((alert_text, 'trade'))
                            last_alerted_pattern_time[alert_key] = latest_pattern_timestamp
        except Exception as e:
            print(f"    - CRITICAL ERROR during LTF scan on {symbol}/{timeframe}: {e}")
            traceback.print_exc()

    return alerts_to_send


async def run_scanner(app: Application):
    """
    The main background task that runs the analysis for all symbols.
    It offloads the blocking analysis for each symbol to a separate thread.
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
            alert_sent_in_cycle = False

            for symbol in symbols_to_scan:
                # Run the blocking analysis in a separate thread
                alerts = await asyncio.to_thread(
                    analyze_symbol_sync, symbol, client, last_alerted_pattern_time
                )

                if user_id and alerts:
                    for alert_text, alert_type in alerts:
                        await app.bot.send_message(chat_id=user_id, text=alert_text, parse_mode='Markdown')
                        if alert_type == 'trade':
                            alert_sent_in_cycle = True

            if user_id and not alert_sent_in_cycle:
                await app.bot.send_message(chat_id=user_id, text=f"✅ اكتمل الفحص. لا توجد فرص جديدة.", disable_notification=True)

            print("Scan cycle complete.")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            print("Background scanner stopped.")
            break
        except Exception as e:
            print(f"An error occurred in the main scanner loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)
