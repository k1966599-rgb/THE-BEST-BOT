import sys
import os
import argparse
from datetime import datetime
import time
import copy
import traceback
import concurrent.futures
from typing import List, Optional
import threading

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_bot import ComprehensiveTradingBot
from config import get_config, WATCHLIST
from telegram_sender import send_telegram_message
from report_generator import generate_final_report_text
from okx_data import OKXDataFetcher, validate_symbol_timeframe

def run_analysis_for_timeframe(symbol: str, timeframe: str, config: dict, okx_fetcher: OKXDataFetcher) -> dict:
    """Runs the complete analysis for a single symbol on a specific timeframe."""
    try:
        # First, validate if the timeframe is supported for the symbol
        validate_symbol_timeframe(symbol, timeframe)

        print(f"--- ⏳ Analyzing {symbol} on {timeframe} ---")
        timeframe_config = copy.deepcopy(config)
        timeframe_config['trading']['INTERVAL'] = timeframe

        bot = ComprehensiveTradingBot(symbol=symbol, config=timeframe_config, okx_fetcher=okx_fetcher)
        bot.run_complete_analysis()
        bot.final_recommendation['timeframe'] = timeframe
        return {'success': True, 'bot': bot}
    except Exception as e:
        print(f"❌ Exception during analysis of {symbol} on {timeframe}:")
        # We don't print the full traceback for validation errors as they are expected.
        if not isinstance(e, ValueError):
            traceback.print_exc()
        return {'success': False, 'timeframe': timeframe, 'error': str(e)}

def rank_opportunities(results: list) -> list:
    """Ranks analysis results from different timeframes."""
    for res in results:
        if res.get('success'):
            rec = res['bot'].final_recommendation
            signal_multiplier = 0.5 if 'انتظار' in rec.get('main_action', '') else 1.0
            rank_score = abs(rec.get('total_score', 0)) * (rec.get('confidence', 0) / 100) * signal_multiplier
            res['rank_score'] = rank_score
        else:
            res['rank_score'] = -1
    return sorted(results, key=lambda x: x.get('rank_score', -1), reverse=True)

def get_top_20_symbols(okx_fetcher: OKXDataFetcher) -> List[str]:
    """Fetches all tickers and returns the top 20 by USDT volume."""
    # This functionality is simplified as the main focus is the bot's analysis engine.
    print("Fetching market tickers to determine top 20 by volume...")
    # In a real scenario, this would involve a call to okx_fetcher
    return WATCHLIST

def get_ranked_analysis_for_symbol(symbol: str, config: dict, okx_fetcher: OKXDataFetcher, timeframes_to_analyze: Optional[List[str]] = None, analysis_type: str = "تحليل مخصص") -> str:
    """
    Performs multi-timeframe analysis in parallel and returns a single, formatted report string.
    """
    if timeframes_to_analyze:
        timeframes = timeframes_to_analyze
    else:
        timeframes = config['trading'].get('TIMEFRAMES_TO_ANALYZE', ['1d'])

    print(f"📊 Starting PARALLEL analysis for {symbol} on {len(timeframes)} timeframes: {timeframes}...")

    all_timeframe_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(timeframes)) as executor:
        future_to_tf = {executor.submit(run_analysis_for_timeframe, symbol, tf, config, okx_fetcher): tf for tf in timeframes}
        for future in concurrent.futures.as_completed(future_to_tf):
            tf = future_to_tf[future]
            try:
                result = future.result()
                all_timeframe_results.append(result)
            except Exception as exc:
                print(f'❌ Timeframe {tf} for {symbol} generated an exception: {exc}')
                # Optionally, append a failure result to still show it in the report
                all_timeframe_results.append({'success': False, 'timeframe': tf, 'error': str(exc)})

    # Filter out only successful results for ranking, but we could also rank failures low
    successful_results = [r for r in all_timeframe_results if r.get('success')]
    if not successful_results:
         # If all timeframes failed, return an error report
         return f"❌ تعذر تحليل {symbol} لجميع الأطر الزمنية المطلوبة."

    ranked_results = rank_opportunities(successful_results)

    final_report = generate_final_report_text(
        symbol=symbol,
        analysis_type=analysis_type,
        ranked_results=ranked_results
    )
    return final_report

def main():
    parser = argparse.ArgumentParser(description='🤖 Comprehensive Technical Analysis Bot (CLI)')
    parser.add_argument('symbols', nargs='*', help='Currency symbols to analyze (e.g., BTC/USDT)')
    parser.add_argument('--watchlist', action='store_true', help='Analyze the default watchlist')

    analysis_group = parser.add_mutually_exclusive_group()
    analysis_group.add_argument('--long', action='store_true', help='Run long-term analysis')
    analysis_group.add_argument('--medium', action='store_true', help='Run medium-term analysis')
    analysis_group.add_argument('--short', action='store_true', help='Run short-term analysis')

    args = parser.parse_args()
    config = get_config()

    # Determine analysis type and timeframes from args
    timeframe_groups = config['trading']['TIMEFRAME_GROUPS']
    if args.long:
        analysis_type = "استثمار طويل المدى (1D - 4H - 1H)"
        timeframes = timeframe_groups['long']
    elif args.medium:
        analysis_type = "تداول متوسط المدى (30m - 15m)"
        timeframes = timeframe_groups['medium']
    elif args.short:
        analysis_type = "مضاربة سريعة (5m - 3m)"
        timeframes = timeframe_groups['short']
    else:
        # Default behavior
        analysis_type = "تحليل افتراضي"
        timeframes = config['trading']['TIMEFRAMES_TO_ANALYZE']

    print("🚀 Initializing OKX Data Fetcher...")
    okx_fetcher = OKXDataFetcher()

    symbols_to_analyze = args.symbols if args.symbols else WATCHLIST if args.watchlist else [config['trading']['DEFAULT_SYMBOL']]

    okx_symbols = [s.replace('/', '-') for s in symbols_to_analyze]
    okx_fetcher.start_data_services(okx_symbols)

    print("⏳ Waiting 10 seconds for initial data...")
    time.sleep(10)

    try:
        for symbol in symbols_to_analyze:
            final_report = get_ranked_analysis_for_symbol(symbol, config, okx_fetcher, timeframes, analysis_type)
            print(final_report)
            send_telegram_message(final_report)
            if len(symbols_to_analyze) > 1:
                time.sleep(5)
    finally:
        print("⏹️ Stopping OKX Data Fetcher...")
        okx_fetcher.stop()

if __name__ == "__main__":
    main()
