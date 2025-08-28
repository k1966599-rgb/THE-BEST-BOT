import logging
import pandas as pd
import datetime
from pybit.unified_trading import HTTP
from typing import Optional, Union

from src.utils.data_quality import clean_market_data

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BybitClient:
    """
    A client for interacting with the Bybit API, focused on fetching market data.
    """
    def __init__(self):
        """Initializes the BybitClient and the HTTP session."""
        self.session = HTTP(testnet=False)
        logging.info("BybitClient initialized.")

    def get_historical_data(self, symbol: str, interval: Union[int, str], total_candles: int = 5000) -> Optional[pd.DataFrame]:
        """
        Fetches and cleans historical k-line data.
        """
        try:
            all_data = []
            limit = 1000

            if str(interval) == 'D':
                start_time = int(datetime.datetime(2022, 1, 1, 0, 0).timestamp() * 1000)
                page_count = 0
                max_pages = 10 # Safety break

                while page_count < max_pages:
                    kline = self.session.get_kline(
                        category="spot", symbol=symbol, interval=str(interval),
                        limit=limit, startTime=start_time
                    )
                    if not (kline and kline.get('retCode') == 0 and kline.get('result', {}).get('list')):
                        break

                    new_data = kline['result']['list']
                    all_data.extend(new_data)

                    if len(new_data) < limit:
                        break

                    start_time = int(new_data[-1][0]) + (60 * 1000)
                    page_count += 1
            else:
                end_time = None
                while len(all_data) < total_candles:
                    kline = self.session.get_kline(
                        category="spot", symbol=symbol, interval=str(interval),
                        limit=limit, endTime=end_time
                    )
                    if not (kline and kline.get('retCode') == 0 and kline.get('result', {}).get('list')):
                        break

                    new_data = kline['result']['list']
                    all_data.extend(new_data)

                    oldest_timestamp = int(new_data[-1][0])
                    end_time = oldest_timestamp - 1

                    if len(new_data) < limit:
                        break
                all_data.reverse()

            if not all_data:
                logging.warning(f"Could not fetch any k-line data for {symbol}")
                return None

            df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(float), unit='ms')

            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])

            logging.info(f"Successfully fetched {len(df)} candles for {symbol} on interval {interval}. Cleaning data...")

            df = clean_market_data(df, str(interval))

            return df

        except Exception as e:
            logging.error(f"Exception while fetching historical data for {symbol}: {e}", exc_info=True)
            return None

    def get_market_price(self, symbol: str) -> Optional[str]:
        """Fetches the last price for a given symbol from Bybit."""
        try:
            result = self.session.get_tickers(category="spot", symbol=symbol)
            if result and result.get('retCode') == 0 and result.get('result', {}).get('list'):
                price = result['result']['list'][0]['lastPrice']
                return price
            else:
                logging.warning(f"Failed to fetch price for {symbol}. Response: {result}")
                return None
        except Exception as e:
            logging.error(f"Exception while fetching price for {symbol}: {e}", exc_info=True)
            return None
