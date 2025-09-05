import pandas as pd
import ccxt
from datetime import datetime, timedelta
import warnings
from typing import Dict, List

from indicators import TechnicalIndicators
from trends import TrendAnalysis
from channels import PriceChannels
from support_resistance import SupportResistanceAnalysis
from fibonacci import FibonacciAnalysis
from classic_patterns import ClassicPatterns
from trade_management import TradeManagement
from okx_data import OKXDataFetcher

warnings.filterwarnings('ignore')

class ComprehensiveTradingBot:
    """
    This class is the core analysis engine. It runs all analysis modules
    for a SINGLE symbol and a SINGLE timeframe, using data from OKXDataFetcher.
    """
    def __init__(self, symbol: str, config: dict, okx_fetcher: OKXDataFetcher):
        self.symbol = symbol.upper()
        self.config = config
        self.okx_fetcher = okx_fetcher
        self.df = None
        self.analysis_results = {}
        self.final_recommendation = {}

    def fetch_data(self) -> bool:
        """
        Fetches historical data for the required timeframe using the OKXDataFetcher.
        This method will use cached data if available, or fetch it if not.
        """
        okx_symbol = self.symbol.replace('/', '-')
        timeframe = self.config['trading']['INTERVAL']
        # Convert to OKX API format.
        # m = minutes, H = hours, D = Days. OKX is specific.
        if 'd' in timeframe:
            api_timeframe = timeframe.replace('d', 'D')
        elif 'h' in timeframe:
            api_timeframe = timeframe.replace('h', 'H')
        else:
            # For minutes (e.g., '1m', '30m'), OKX uses lowercase 'm'. No change needed.
            api_timeframe = timeframe

        print(f"Fetching historical data for {okx_symbol} on timeframe {api_timeframe} via OKXDataFetcher...")

        # The number of days to fetch can be derived from the 'PERIOD' config
        period_str = self.config['trading'].get('PERIOD', '1y')
        unit = ''.join(filter(str.isalpha, period_str)).lower()
        num = int(''.join(filter(str.isdigit, period_str)))

        if unit == 'y':
            days = num * 365
        elif unit == 'mo':
            days = num * 30
        elif unit == 'w':
            days = num * 7
        elif unit == 'd':
            days = num
        else: # Default to days if unit is unrecognized
            days = num

        historical_data = self.okx_fetcher.fetch_historical_data(
            symbol=okx_symbol,
            timeframe=api_timeframe,
            days_to_fetch=days
        )

        if not historical_data:
            print(f"Error: Could not fetch historical data for {okx_symbol} on {timeframe}.")
            return False

        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        self.df = df.dropna()
        return True

    def run_all_analyses(self):
        modules = {
            'indicators': TechnicalIndicators,
            'trends': TrendAnalysis,
            'channels': PriceChannels,
            'support_resistance': SupportResistanceAnalysis,
            'fibonacci': FibonacciAnalysis,
            'patterns': ClassicPatterns
        }
        analysis_config = self.config.get('analysis', {})
        for name, module_class in modules.items():
            try:
                # Note: The comprehensive analysis method name is slightly different for some modules
                # Standardize method names for clarity
                if name == 'support_resistance':
                    method_name = 'get_comprehensive_sr_analysis'
                elif name == 'patterns':
                    # Use the new, more descriptive method name from the enhanced module
                    method_name = 'get_comprehensive_patterns_analysis'
                else:
                    method_name = f'get_comprehensive_{name}_analysis'

                instance = module_class(self.df, config=analysis_config)
                self.analysis_results[name] = getattr(instance, method_name)()
            except Exception as e:
                self.analysis_results[name] = {'error': str(e), 'total_score': 0, 'sr_score': 0, 'fib_score': 0, 'pattern_score': 0}

    def run_trade_management_analysis(self):
        try:
            tm = TradeManagement(self.df, self.config['trading']['ACCOUNT_BALANCE'])
            self.analysis_results['trade_management'] = tm.get_comprehensive_trade_plan(self.final_recommendation, self.analysis_results)
        except Exception as e: self.analysis_results['trade_management'] = {'error': str(e)}

    def calculate_final_recommendation(self):
        scores = {
            'indicators': self.analysis_results.get('indicators', {}).get('total_score', 0),
            'trends': self.analysis_results.get('trends', {}).get('total_score', 0),
            'channels': self.analysis_results.get('channels', {}).get('total_score', 0),
            'support_resistance': self.analysis_results.get('support_resistance', {}).get('sr_score', 0),
            'fibonacci': self.analysis_results.get('fibonacci', {}).get('fib_score', 0),
            'patterns': self.analysis_results.get('patterns', {}).get('pattern_score', 0),
        }
        total_score = sum(scores.values())
        if total_score >= 10: main_action, confidence = "شراء قوي 🚀", 95
        elif total_score >= 5: main_action, confidence = "شراء 📈", 85
        elif total_score >= -2: main_action, confidence = "انتظار ⏳", 60
        elif total_score >= -6: main_action, confidence = "بيع 📉", 85
        else: main_action, confidence = "بيع قوي 🔻", 95

        # Get live price from the fetcher's cache
        okx_symbol = self.symbol.replace('/', '-')
        live_price_data = self.okx_fetcher.get_cached_price(okx_symbol)

        # Fallback to the last close price from historical data if live price is not available
        current_price = live_price_data['price'] if live_price_data else self.df['close'].iloc[-1]

        self.final_recommendation = {'symbol': self.symbol, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'current_price': current_price, 'main_action': main_action, 'confidence': confidence, 'total_score': total_score, 'individual_scores': scores}

    def run_complete_analysis(self):
        """
        Runs the full analysis pipeline for the configured symbol and timeframe.
        This class no longer generates the report string itself.
        """
        print(f"🚀 Running analysis for {self.symbol}...")
        if not self.fetch_data():
            raise ConnectionError(f"Failed to fetch data for {self.symbol}")

        self.run_all_analyses()
        self.calculate_final_recommendation()
        self.run_trade_management_analysis()
        print(f"✅ Analysis complete for {self.symbol}.")
