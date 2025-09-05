#!/usr/bin/env python3
"""
OKX Data Fetcher - جامع البيانات المباشرة من منصة OKX
متخصص لمشاريع Python
"""

import asyncio
import websockets
import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# إعداد التسجيل
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
    """جامع البيانات المباشرة من منصة OKX"""

    def __init__(self, data_dir: str = 'okx_data'):
        self.base_url = 'https://www.okx.com'
        self.ws_url = 'wss://ws.okx.com:8443/ws/v5/public'
        self.data_dir = Path(data_dir)
        self.price_cache = {}
        self.historical_cache = {}
        self.ws_connection = None
        self.is_connected = False
        self.reconnect_interval = 5
        self._stop_event = threading.Event()

        # العملات الافتراضية
        self.default_symbols = [
            'BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'XRP-USDT',
            'ADA-USDT', 'SOL-USDT', 'DOT-USDT', 'DOGE-USDT',
            'MATIC-USDT', 'LTC-USDT', 'LINK-USDT', 'UNI-USDT'
        ]

        # إنشاء مجلد البيانات
        self._ensure_data_directory()
        logger.info(f"📁 تم إنشاء جامع بيانات OKX - مجلد البيانات: {self.data_dir}")

    def _ensure_data_directory(self):
        """إنشاء مجلد البيانات"""
        try:
            self.data_dir.mkdir(exist_ok=True)
            logger.info(f"📁 مجلد البيانات جاهز: {self.data_dir}")
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء مجلد البيانات: {e}")

    def fetch_current_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Fetches current prices.
        If symbols is None, fetches for the default list.
        If symbols is an empty list, fetches for ALL available SPOT tickers.
        """
        fetch_all = symbols == []
        symbol_list = self.default_symbols if symbols is None else symbols

        try:
            log_message = "all available tickers" if fetch_all else f"prices for {symbol_list}"
            logger.info(f"💰 Fetching current {log_message}...")

            response = requests.get(
                f"{self.base_url}/api/v5/market/tickers",
                params={'instType': 'SPOT'},
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                timeout=15 # Increased timeout for potentially large response
            )

            if response.status_code == 200:
                data = response.json()

                if data.get('code') == '0':
                    all_tickers = data.get('data', [])
                    processed_prices = {}

                    # Determine which tickers to process
                    tickers_to_process = all_tickers if fetch_all else [t for t in all_tickers if t['instId'] in symbol_list]

                    for ticker in tickers_to_process:
                        symbol = ticker['instId']
                        price_data = {
                            'symbol': symbol,
                            'price': float(ticker['last']),
                            'change_24h': float(ticker.get('chg24h', 0)),
                            'change_percent': float(ticker.get('chgPct24h', 0)),
                            'high_24h': float(ticker.get('high24h', 0)),
                            'low_24h': float(ticker.get('low24h', 0)),
                            'volume': float(ticker.get('vol24h', 0)),
                            'timestamp': int(ticker.get('ts', 0)),
                            'last_update': datetime.now().isoformat()
                        }
                        processed_prices[symbol] = price_data
                        self.price_cache[symbol] = price_data # Update cache

                    self._save_price_data(processed_prices)
                    logger.info(f"✅ Fetched prices for {len(processed_prices)} symbols.")

                    return processed_prices
                else:
                    raise Exception(f"خطأ من API: {data.get('msg', 'غير معروف')}")
            else:
                raise Exception(f"HTTP Error: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ خطأ في جلب الأسعار الحالية: {e}")
            return {}

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Converts an OKX timeframe string to minutes for estimations."""
        try:
            if timeframe.endswith('m'):
                return int(timeframe[:-1])
            if timeframe.endswith('H'):
                return int(timeframe[:-1]) * 60
            if timeframe.endswith('D'):
                return int(timeframe[:-1]) * 24 * 60
        except Exception:
            # Fallback for common cases if parsing fails, e.g., '1D' vs '1d'
            if 'D' in timeframe.upper(): return 1440
            if 'H' in timeframe.upper(): return 240
        return 1 # Default to 1 minute to avoid division by zero errors

    def fetch_historical_data(self, symbol: str = 'BTC-USDT', timeframe: str = '1D', days_to_fetch: int = 365) -> List[Dict]:
        """Fetches historical data by paginating backwards from the current time."""
        try:
            logger.info(f"📊 Fetching historical data for {symbol} for the last {days_to_fetch} days...")

            all_candles = []
            # For the first request, 'before' is None to get the latest data.
            # For subsequent requests, it will be the timestamp of the last fetched candle.
            current_before_ts = None
            endpoint_url = f"{self.base_url}/api/v5/market/candles"
            limit_per_request = 100

            # Approximate the number of requests needed to get the desired number of days
            tf_minutes = self._timeframe_to_minutes(timeframe)
            if tf_minutes <= 0: tf_minutes = 1440 # Default to 1 day if something is wrong
            total_candles_needed = (days_to_fetch * 24 * 60) / tf_minutes
            num_requests = int(total_candles_needed / limit_per_request) + 2

            for i in range(num_requests):
                params = {
                    'instId': symbol,
                    'bar': timeframe,
                    'limit': str(limit_per_request)
                }
                if current_before_ts:
                    params['before'] = current_before_ts

                logger.info(f"Requesting chunk {i+1}/{num_requests} from OKX API with params: {params}")

                response = requests.get(
                    endpoint_url,
                    params=params,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                    timeout=15
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('code') == '0':
                        candles_data = data.get('data', [])
                        if not candles_data:
                            logger.info("API returned no more candle data. Stopping fetch.")
                            break

                        all_candles.extend(candles_data)
                        current_before_ts = candles_data[-1][0]
                        time.sleep(0.25)
                    else:
                        raise Exception(f"API Error: {data.get('msg', 'Unknown error')}")
                else:
                    raise Exception(f"HTTP Error: {response.status_code} - {response.text}")

            # Process all fetched candles
            historical_data = []
            seen_timestamps = set()
            for candle in all_candles:
                timestamp = int(candle[0])
                if timestamp not in seen_timestamps:
                    historical_data.append({
                        'timestamp': timestamp,
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5]),
                        'date': datetime.fromtimestamp(timestamp / 1000).isoformat()
                    })
                    seen_timestamps.add(timestamp)

            # Sort data by timestamp ascending
            historical_data.sort(key=lambda x: x['timestamp'])

            # Save and cache the data
            self._save_historical_data(symbol, historical_data)
            self.historical_cache[symbol] = historical_data

            logger.info(f"✅ تم جلب {len(historical_data)} شمعة تاريخية فريدة لـ {symbol}")
            return historical_data

        except Exception as e:
            logger.error(f"❌ خطأ في جلب البيانات التاريخية لـ {symbol}: {e}")
            return []

    async def start_websocket(self, symbols: List[str] = None):
        """بدء اتصال WebSocket للبيانات المباشرة"""
        if symbols is None:
            symbols = self.default_symbols

        while not self._stop_event.is_set():
            try:
                logger.info("🔗 محاولة الاتصال بـ WebSocket...")

                async with websockets.connect(self.ws_url) as websocket:
                    self.ws_connection = websocket
                    self.is_connected = True
                    logger.info("✅ تم الاتصال بـ WebSocket")

                    # الاشتراك في تحديثات الأسعار
                    subscribe_message = {
                        "op": "subscribe",
                        "args": [{"channel": "tickers", "instId": symbol} for symbol in symbols]
                    }

                    await websocket.send(json.dumps(subscribe_message))
                    logger.info(f"📡 تم الاشتراك في {len(symbols)} رمز عملة")

                    # Receive messages
                    while not self._stop_event.is_set():
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            data = json.loads(message)
                            if 'data' in data and data.get('data'):
                                await self._process_websocket_data(data['data'])
                        except asyncio.TimeoutError:
                            # No message received, which is fine. This allows the loop to check the stop event.
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed. Attempting to reconnect...")
                            break
                        except Exception as e:
                            logger.error(f"❌ Error processing WebSocket message: {e}")

            except Exception as e:
                logger.error(f"❌ WebSocket error: {e}")
            finally:
                self.is_connected = False
                if not self._stop_event.is_set():
                    logger.info(f"⏳ Reconnecting in {self.reconnect_interval} seconds...")
                    await asyncio.sleep(self.reconnect_interval)

    async def _process_websocket_data(self, data_list: List[Dict]):
        """معالجة بيانات WebSocket"""
        try:
            for ticker in data_list:
                price_data = {
                    'symbol': ticker['instId'],
                    'price': float(ticker['last']),
                    'change_24h': float(ticker.get('chg24h', 0)),
                    'change_percent': float(ticker.get('chgPct24h', 0)),
                    'high_24h': float(ticker.get('high24h', 0)),
                    'low_24h': float(ticker.get('low24h', 0)),
                    'volume': float(ticker.get('vol24h', 0)),
                    'timestamp': int(ticker.get('ts', 0)),
                    'last_update': datetime.now().isoformat()
                }

                # تحديث الكاش
                self.price_cache[ticker['instId']] = price_data

                # طباعة التحديث
                change_icon = '📈' if price_data['change_percent'] >= 0 else '📉'
                logger.info(
                    f"{change_icon} {ticker['instId']}: ${price_data['price']:.4f} "
                    f"({'+' if price_data['change_percent'] >= 0 else ''}{price_data['change_percent']:.2f}%)"
                )

            # حفظ التحديثات
            self._save_price_data(self.price_cache)

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة بيانات WebSocket: {e}")

    def _save_price_data(self, prices: Dict[str, Any]):
        """حفظ أسعار اللحظة الحالية"""
        try:
            filename = self.data_dir / 'current_prices.json'
            data_to_save = {
                'prices': prices,
                'last_update': datetime.now().isoformat(),
                'total_symbols': len(prices)
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ خطأ في حفظ بيانات الأسعار: {e}")

    def _save_historical_data(self, symbol: str, data: List[Dict]):
        """حفظ البيانات التاريخية"""
        try:
            filename = self.data_dir / f"{symbol.replace('/', '-')}_historical.json"
            data_to_save = {
                'symbol': symbol,
                'data': data,
                'last_update': datetime.now().isoformat(),
                'total_records': len(data)
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 تم حفظ البيانات التاريخية: {filename}")

        except Exception as e:
            logger.error(f"❌ خطأ في حفظ البيانات التاريخية لـ {symbol}: {e}")

    def get_cached_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """جلب السعر من الكاش"""
        return self.price_cache.get(symbol)

    def get_cached_historical_data(self, symbol: str) -> Optional[List[Dict]]:
        """جلب البيانات التاريخية من الكاش"""
        return self.historical_cache.get(symbol)

    def analyze_trend(self, symbol: str, period: int = 20) -> Dict[str, Any]:
        """تحليل الاتجاه بناءً على البيانات التاريخية"""
        historical = self.get_cached_historical_data(symbol)

        if not historical or len(historical) < period:
            return {'trend': 'غير كافي', 'confidence': 0, 'sma': None}

        # أخذ البيانات الحديثة
        recent_data = historical[-period:]
        prices = [d['close'] for d in recent_data]

        # حساب المتوسط المتحرك البسيط
        sma = sum(prices) / len(prices)
        current_price_data = self.get_cached_price(symbol)
        current_price = current_price_data['price'] if current_price_data else prices[-1]

        # تحديد الاتجاه
        trend = 'جانبي'
        confidence = 0

        if current_price > sma * 1.02:
            trend = 'صاعد'
            confidence = min(((current_price - sma) / sma) * 100, 100)
        elif current_price < sma * 0.98:
            trend = 'هابط'
            confidence = min(((sma - current_price) / sma) * 100, 100)

        return {
            'trend': trend,
            'confidence': round(confidence),
            'sma': round(sma, 2),
            'current_price': current_price,
            'analysis_time': datetime.now().isoformat()
        }

    def calculate_rsi(self, symbol: str, period: int = 14) -> Optional[float]:
        """حساب مؤشر القوة النسبية RSI"""
        historical = self.get_cached_historical_data(symbol)

        if not historical or len(historical) < period + 1:
            return None

        prices = [d['close'] for d in historical[-period-1:]]

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(change if change > 0 else 0)
            losses.append(abs(change) if change < 0 else 0)

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def get_trading_signals(self, symbol: str) -> Dict[str, Any]:
        """الحصول على إشارات التداول"""
        trend = self.analyze_trend(symbol)
        rsi = self.calculate_rsi(symbol)
        current_price = self.get_cached_price(symbol)

        signals = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price': current_price['price'] if current_price else None,
            'trend': trend,
            'rsi': rsi,
            'signals': []
        }

        # إشارات التداول
        if rsi and rsi < 30 and trend['trend'] == 'صاعد':
            signals['signals'].append({
                'type': 'شراء قوي',
                'reason': 'RSI منخفض + اتجاه صاعد',
                'confidence': min(trend['confidence'] + 20, 100)
            })
        elif rsi and rsi > 70 and trend['trend'] == 'هابط':
            signals['signals'].append({
                'type': 'بيع قوي',
                'reason': 'RSI مرتفع + اتجاه هابط',
                'confidence': min(trend['confidence'] + 20, 100)
            })
        elif rsi and rsi < 35:
            signals['signals'].append({
                'type': 'شراء',
                'reason': 'RSI منخفض',
                'confidence': 60
            })
        elif rsi and rsi > 65:
            signals['signals'].append({
                'type': 'بيع',
                'reason': 'RSI مرتفع',
                'confidence': 60
            })

        return signals

    def get_market_overview(self) -> Dict[str, Any]:
        """نظرة عامة على السوق"""
        overview = {
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(self.price_cache),
            'connected': self.is_connected,
            'top_gainers': [],
            'top_losers': [],
            'market_summary': {
                'bullish': 0,
                'bearish': 0,
                'neutral': 0
            }
        }

        # تحليل العملات
        symbol_analysis = []
        for symbol in self.default_symbols:
            price_data = self.get_cached_price(symbol)
            if price_data:
                trend = self.analyze_trend(symbol)
                symbol_analysis.append({
                    'symbol': symbol,
                    'change_percent': price_data['change_percent'],
                    'trend': trend['trend']
                })

        # ترتيب الرابحين والخاسرين
        symbol_analysis.sort(key=lambda x: x['change_percent'], reverse=True)
        overview['top_gainers'] = symbol_analysis[:5]
        overview['top_losers'] = symbol_analysis[-5:]

        # ملخص السوق
        for analysis in symbol_analysis:
            if analysis['trend'] == 'صاعد':
                overview['market_summary']['bullish'] += 1
            elif analysis['trend'] == 'هابط':
                overview['market_summary']['bearish'] += 1
            else:
                overview['market_summary']['neutral'] += 1

        return overview

    def start_full_data_collection(self, symbols: List[str] = None):
        """بدء جمع البيانات الشاملة"""
        if symbols is None:
            symbols = self.default_symbols

        logger.info("🚀 بدء جمع البيانات الشاملة...")

        # جلب البيانات التاريخية في thread منفصل
        def fetch_all_historical():
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for symbol in symbols:
                    future = executor.submit(self.fetch_historical_data, symbol)
                    futures.append(future)
                    time.sleep(0.1)  # تأخير قصير بين الطلبات

                # انتظار انتهاء جميع المهام
                for future in futures:
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"❌ خطأ في جلب البيانات التاريخية: {e}")

        # بدء جلب البيانات التاريخية
        historical_thread = threading.Thread(target=fetch_all_historical)
        historical_thread.start()

        # جلب الأسعار الحالية
        self.fetch_current_prices(symbols)

        # بدء WebSocket في thread منفصل
        def start_ws():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_websocket(symbols))

        ws_thread = threading.Thread(target=start_ws)
        ws_thread.daemon = True
        ws_thread.start()

        # انتظار انتهاء جلب البيانات التاريخية
        historical_thread.join()

        logger.info("✅ تم بدء جمع البيانات بنجاح!")

    def stop(self):
        """Signals all running threads to stop."""
        logger.info("⏹️ Stopping data fetcher...")
        self._stop_event.set()
        self.is_connected = False
        # The websocket thread will see the event and exit gracefully.
        logger.info("✅ Stop signal sent to data fetcher.")

# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء جامع البيانات
    okx_fetcher = OKXDataFetcher()

    try:
        # بدء جمع البيانات
        symbols = ['BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'XRP-USDT']
        okx_fetcher.start_full_data_collection(symbols)

        # انتظار قصير للحصول على البيانات
        time.sleep(10)

        # عرض مثال على البيانات
        print("\n📊 مثال على البيانات:")
        btc_price = okx_fetcher.get_cached_price('BTC-USDT')
        if btc_price:
            print(f"🪙 BTC: ${btc_price['price']:.2f} ({btc_price['change_percent']:+.2f}%)")

        # تحليل الاتجاه
        btc_analysis = okx_fetcher.analyze_trend('BTC-USDT')
        print(f"📈 BTC الاتجاه: {btc_analysis['trend']} (ثقة: {btc_analysis['confidence']}%)")

        # إشارات التداول
        signals = okx_fetcher.get_trading_signals('BTC-USDT')
        if signals['signals']:
            for signal in signals['signals']:
                print(f"🎯 إشارة: {signal['type']} - {signal['reason']} (ثقة: {signal['confidence']}%)")

        # نظرة عامة على السوق
        overview = okx_fetcher.get_market_overview()
        print(f"\n📊 ملخص السوق:")
        print(f"   📈 صاعد: {overview['market_summary']['bullish']}")
        print(f"   📉 هابط: {overview['market_summary']['bearish']}")
        print(f"   ➡️ جانبي: {overview['market_summary']['neutral']}")

        # إبقاء البرنامج يعمل
        print("\n⌨️ اضغط Ctrl+C للإيقاف...")
        try:
            while True:
                time.sleep(60)  # تحديث كل دقيقة
                overview = okx_fetcher.get_market_overview()
                print(f"🔄 {datetime.now().strftime('%H:%M:%S')} - عدد العملات: {overview['total_symbols']} | متصل: {'✅' if overview['connected'] else '❌'}")
        except KeyboardInterrupt:
            pass

    except Exception as e:
        logger.error(f"❌ خطأ في البرنامج الرئيسي: {e}")
    finally:
        okx_fetcher.stop()
