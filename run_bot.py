import sys
import os
import argparse
from datetime import datetime
import time
import copy
import traceback
import concurrent.futures

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import threading
try:
    from main_bot import ComprehensiveTradingBot
    from config import get_config, WATCHLIST
    from telegram_sender import send_telegram_message
    from report_generator import generate_full_report
    from okx_data import OKXDataFetcher
except ImportError as e:
    print(f"❌ خطأ في استيراد الوحدات: {e}")
    sys.exit(1)

def run_analysis_for_timeframe(symbol: str, timeframe: str, config: dict, okx_fetcher: OKXDataFetcher) -> dict:
    """Runs the complete analysis for a single symbol on a specific timeframe."""
    print(f"--- ⏳ تحليل {symbol} على فريم {timeframe} ---")
    timeframe_config = copy.deepcopy(config)
    timeframe_config['trading']['INTERVAL'] = timeframe
    try:
        bot = ComprehensiveTradingBot(symbol=symbol, config=timeframe_config, okx_fetcher=okx_fetcher)
        bot.run_complete_analysis()
        bot.final_recommendation['timeframe'] = timeframe
        return {'success': True, 'bot': bot}
    except Exception as e:
        # Add detailed exception logging for debugging
        print(f"❌ An exception occurred during analysis of {symbol} on {timeframe}:")
        traceback.print_exc()
        return {'success': False, 'timeframe': timeframe, 'error': str(e)}

def rank_opportunities(results: list) -> list:
    """Ranks analysis results from different timeframes."""
    for res in results:
        if res['success']:
            rec = res['bot'].final_recommendation
            signal_multiplier = 0.5 if 'انتظار' in rec.get('main_action', '') else 1.0
            rank_score = abs(rec.get('total_score', 0)) * (rec.get('confidence', 0) / 100) * signal_multiplier
            res['rank_score'] = rank_score
        else:
            res['rank_score'] = -1
    return sorted(results, key=lambda x: x.get('rank_score', -1), reverse=True)

from typing import List, Optional

def get_top_20_symbols(okx_fetcher: OKXDataFetcher) -> List[str]:
    """Fetches all tickers and returns the top 20 by USDT volume."""
    print("Fetching all market tickers to determine top 20 by volume...")
    # Pass empty list to fetch all tickers
    all_tickers = okx_fetcher.fetch_current_prices(symbols=[])
    if not all_tickers:
        print("Could not fetch market tickers. Falling back to default watchlist.")
        return WATCHLIST

    # Filter for USDT pairs and sort by 24h volume (vol24h field)
    usdt_tickers = [t for t in all_tickers.values() if t['symbol'].endswith('-USDT')]

    # Sort by volume, which is in the base currency. For USDT pairs, this is what we want.
    sorted_tickers = sorted(usdt_tickers, key=lambda x: x['volume'], reverse=True)

    # Get the top 20 symbols and convert them back to 'BTC/USDT' format for the bot
    top_20_symbols = [t['symbol'].replace('-', '/') for t in sorted_tickers[:20]]
    print(f"Top 20 symbols by volume: {top_20_symbols}")
    return top_20_symbols

def get_ranked_analysis_for_symbol(symbol: str, config: dict, okx_fetcher: OKXDataFetcher, timeframes_to_analyze: Optional[List[str]] = None) -> str:
    """
    Performs multi-timeframe analysis in parallel and returns a single, formatted report string.
    Can analyze a specific list of timeframes if provided, otherwise uses the default from config.
    """
    if timeframes_to_analyze:
        timeframes = timeframes_to_analyze
    else:
        timeframes = config['trading'].get('TIMEFRAMES_TO_ANALYZE', ['1d'])

    print(f"📊 Starting PARALLEL analysis for {symbol} on {len(timeframes)} timeframes: {timeframes}...")

    all_timeframe_results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Use executor.map to run analyses in parallel.
        # The lambda function provides the fixed arguments (symbol, config, fetcher)
        # to the analysis function for each timeframe in the list.
        results_iterator = executor.map(
            lambda tf: run_analysis_for_timeframe(symbol, tf, config, okx_fetcher),
            timeframes
        )
        all_timeframe_results = list(results_iterator)

    ranked_results = rank_opportunities(all_timeframe_results)

    final_report = generate_full_report(
        symbol=symbol,
        exchange=config['trading']['EXCHANGE_ID'],
        ranked_results=ranked_results
    )
    return final_report

def main():
    parser = argparse.ArgumentParser(description='🤖 البوت الشامل للتحليل الفني (CCXT)')
    parser.add_argument('symbols', nargs='*', help='رموز العملات للتحليل (e.g., BTC/USDT)')
    parser.add_argument('--watchlist', action='store_true', help='تحليل قائمة المراقبة')
    parser.add_argument('--top20', action='store_true', help='تحليل أفضل 20 عملة')
    parser.add_argument('--period', type=str, default=None, help="تحديد فترة البيانات (e.g., '3mo', '1y')")
    args = parser.parse_args()
    config = get_config()

    if args.period: config['trading']['PERIOD'] = args.period

    # Initialize the data fetcher
    print("🚀 Initializing OKX Data Fetcher...")
    okx_fetcher = OKXDataFetcher()

    symbols_to_analyze = []
    if args.top20:
        symbols_to_analyze = get_top_20_symbols(okx_fetcher)
    elif args.watchlist:
        symbols_to_analyze = WATCHLIST
    elif args.symbols:
        symbols_to_analyze = [s.upper() for s in args.symbols]
    else:
        symbols_to_analyze = [config['trading']['DEFAULT_SYMBOL']]

    if not symbols_to_analyze:
        sys.exit("❌ لم يتم تحديد عملات للتحليل.")

    # Convert symbols to OKX format (e.g., BTC-USDT) for the fetcher
    okx_symbols = list(set([s.replace('/', '-') for s in symbols_to_analyze]))

    print(f"📡 Starting data collection for {len(okx_symbols)} symbols...")
    fetcher_thread = threading.Thread(target=okx_fetcher.start_full_data_collection, args=(okx_symbols,), daemon=True)
    fetcher_thread.start()

    print("⏳ Waiting 10 seconds for initial data from WebSocket...")
    time.sleep(10)

    try:
        for symbol in symbols_to_analyze:
            final_report = get_ranked_analysis_for_symbol(symbol, config, okx_fetcher)
            print(final_report)
            send_telegram_message(final_report)
            if len(symbols_to_analyze) > 1:
                time.sleep(5)
    finally:
        print("⏹️ Stopping OKX Data Fetcher...")
        okx_fetcher.stop()

if __name__ == "__main__":
    main()
