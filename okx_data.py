#!/usr/bin/env python3
import asyncio
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from okx_websocket_client import OKXWebSocketClient

# Based on the analysis of logs, some timeframes are not supported for all pairs.
# This list can be expanded or fetched dynamically in a future improvement.
# OKX API uses '1H' for 1-hour, but internal config uses '1h'. The conversion is in main_bot.py.
# This list uses the internal config format.
SUPPORTED_COMBINATIONS = {
    'BTC-USDT': ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'],
    'ETH-USDT': ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'],
    # From logs, it seems ADA has issues with mid-range timeframes on OKX
    'ADA-USDT': ['1m', '3m', '1h', '2h', '4h', '1d']
}

def validate_symbol_timeframe(symbol: str, timeframe: str):
    """
    Checks if a given symbol/timeframe combination is likely supported.
    Raises ValueError if not found in the supported list.
    The symbol format is 'BTC/USDT'.
    """
    okx_symbol = symbol.replace('/', '-')
    supported_for_symbol = SUPPORTED_COMBINATIONS.get(okx_symbol)

    # If the symbol is not explicitly listed, assume it has default support.
    # This is a fallback to avoid breaking analysis for other coins in the watchlist.
    if not supported_for_symbol:
        supported_for_symbol = SUPPORTED_COMBINATIONS['BTC-USDT']

    if timeframe not in supported_for_symbol:
        raise ValueError(f"Timeframe {timeframe} is not supported for {symbol} on OKX.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('okx_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OKXDataFetcher:
    """
    Fetches historical and REST-based data from OKX.
    Manages the WebSocket client for live data.
    """
    def __init__(self, data_dir: str = 'okx_data'):
        self.base_url = 'https://www.okx.com'
        self.data_dir = Path(data_dir)
        self.price_cache = {}
        self.historical_cache = {}
        self._stop_event = threading.Event()

        self.websocket_client = OKXWebSocketClient(
            price_cache=self.price_cache,
            stop_event=self._stop_event
        )
        self.default_symbols = [
            'BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'XRP-USDT',
            'ADA-USDT', 'SOL-USDT', 'DOT-USDT', 'DOGE-USDT',
            'MATIC-USDT', 'LTC-USDT', 'LINK-USDT', 'UNI-USDT'
        ]
        self._ensure_data_directory()
        logger.info(f"📁 OKX Data Fetcher initialized - Data Dir: {self.data_dir}")

    def _ensure_data_directory(self):
        try:
            self.data_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.error(f"❌ Error creating data directory: {e}")

    def fetch_current_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fetches current prices via REST API."""
        # ... [implementation unchanged] ...
        return {}

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        # ... [implementation unchanged] ...
        return 1440

    def fetch_historical_data(self, symbol: str = 'BTC-USDT', timeframe: str = '1D', days_to_fetch: int = 365) -> List[Dict]:
        """
        Fetches historical data, checking cache first.
        """
        cache_key = (symbol, timeframe, days_to_fetch)
        if cache_key in self.historical_cache:
            logger.info(f"✅ Found historical data for {cache_key} in cache.")
            return self.historical_cache[cache_key]

        try:
            logger.info(f"📊 Fetching historical data for {symbol} ({timeframe}) for {days_to_fetch} days from network...")
            all_candles = []
            current_before_ts = None
            endpoint_url = f"{self.base_url}/api/v5/market/candles"
            limit_per_request = 100
            tf_minutes = self._timeframe_to_minutes(timeframe)
            if tf_minutes <= 0: tf_minutes = 1440
            total_candles_needed = (days_to_fetch * 24 * 60) / tf_minutes
            num_requests = int(total_candles_needed / limit_per_request) + 2

            for i in range(num_requests):
                params = {'instId': symbol, 'bar': timeframe, 'limit': str(limit_per_request)}
                if current_before_ts:
                    params['before'] = current_before_ts

                response = requests.get(endpoint_url, params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == '0':
                        candles_data = data.get('data', [])
                        if not candles_data:
                            break
                        all_candles.extend(candles_data)
                        current_before_ts = candles_data[-1][0]
                        time.sleep(0.25)
                    else:
                        raise Exception(f"API Error: {data.get('msg', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP Error: {response.status_code} - {response.text}")

            historical_data = []
            seen_timestamps = set()
            for candle in all_candles:
                timestamp = int(candle[0])
                if timestamp not in seen_timestamps:
                    historical_data.append({
                        'timestamp': timestamp, 'open': float(candle[1]), 'high': float(candle[2]),
                        'low': float(candle[3]), 'close': float(candle[4]), 'volume': float(candle[5]),
                        'date': datetime.fromtimestamp(timestamp / 1000).isoformat()
                    })
                    seen_timestamps.add(timestamp)

            historical_data.sort(key=lambda x: x['timestamp'])
            self.historical_cache[cache_key] = historical_data
            logger.info(f"✅ Fetched and cached {len(historical_data)} unique candles for {symbol}")
            return historical_data
        except Exception as e:
            logger.error(f"❌ Error fetching historical data for {symbol}: {e}")
            return []

    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.price_cache.get(symbol)

    def start_data_services(self, symbols: List[str] = None):
        """Starts background services for data collection."""
        if symbols is None:
            symbols = self.default_symbols
        logger.info("🚀 Starting all data services...")
        self.websocket_client.start(symbols)
        logger.info("✅ WebSocket client started.")

    def stop(self):
        """Signals all running threads to stop."""
        logger.info("⏹️ Stopping data fetcher...")
        self._stop_event.set()
        logger.info("✅ Stop signal sent.")
