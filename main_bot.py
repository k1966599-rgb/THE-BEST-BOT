import pandas as pd
import pandas_ta as ta
import ccxt
from datetime import datetime, timedelta
import warnings
from typing import Dict, List

from analysis.indicators import TechnicalIndicators
from analysis.trends import TrendAnalysis
from analysis.channels import PriceChannels
from analysis.support_resistance import SupportResistanceAnalysis
from analysis.fibonacci import FibonacciAnalysis
from analysis.classic_patterns import ClassicPatterns
from trade_management import TradeManagement
from okx_data import OKXDataFetcher

warnings.filterwarnings('ignore')

class ComprehensiveTradingBot:
    def __init__(self, symbol: str, config: dict, okx_fetcher: OKXDataFetcher):
        self.symbol = symbol.upper()
        self.config = config
        self.okx_fetcher = okx_fetcher
        self.df = None
        self.df_with_indicators = None
        self.analysis_results = {}
        self.final_recommendation = {}

    def fetch_data(self) -> bool:
        okx_symbol = self.symbol.replace('/', '-')
        timeframe = self.config['trading']['INTERVAL']
        api_timeframe = timeframe.replace('d', 'D').replace('h', 'H') if 'd' in timeframe or 'h' in timeframe else timeframe

        print(f"Fetching historical data for {okx_symbol} on timeframe {api_timeframe} via OKXDataFetcher...")

        period_str = self.config['trading'].get('PERIOD', '1y')
        unit = ''.join(filter(str.isalpha, period_str)).lower()
        num = int(''.join(filter(str.isdigit, period_str)))
        days = num * 365 if unit == 'y' else num * 30 if unit == 'mo' else num * 7 if unit == 'w' else num

        historical_data = self.okx_fetcher.fetch_historical_data(symbol=okx_symbol, timeframe=api_timeframe, days_to_fetch=days)

        if not historical_data:
            print(f"Error: Could not fetch historical data for {okx_symbol} on {timeframe}.")
            return False

        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        self.df = df.dropna()
        return True

    def _prepare_data_with_indicators(self):
        """
        Calculates all necessary technical indicators once and stores them in a new dataframe.
        This is an efficient design to avoid recalculating indicators in each module.
        """
        if self.df is None: return

        # Create a copy to hold the indicators
        self.df_with_indicators = self.df.copy()
        # Rename columns for pandas_ta compatibility
        self.df_with_indicators.rename(columns={"high": "High", "low": "Low", "open": "Open", "close": "Close", "volume": "Volume"}, inplace=True, errors='ignore')

        # Use the ta.Strategy to build a list of indicators
        MyStrategy = ta.Strategy(
            name="Comprehensive Strategy",
            description="Calculates all indicators needed for the bot",
            ta=[
                {"kind": "sma", "length": 20},
                {"kind": "sma", "length": 50},
                {"kind": "sma", "length": 200},
                {"kind": "ema", "length": 20},
                {"kind": "ema", "length": 50},
                {"kind": "ema", "length": 100},
                {"kind": "rsi"},
                {"kind": "macd"},
                {"kind": "bbands"},
                {"kind": "stoch"},
                {"kind": "atr"},
                {"kind": "obv"},
                {"kind": "adx"},
            ]
        )
        # Run the strategy on the dataframe
        self.df_with_indicators.ta.strategy(MyStrategy)

    def run_all_analyses(self):
        # Ensure we have the dataframe with indicators before running analyses
        if self.df_with_indicators is None:
            self.analysis_results = {'error': "Indicator dataframe not prepared."}
            return

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
                # All modules now receive the same dataframe with pre-calculated indicators
                instance = module_class(self.df_with_indicators, config=analysis_config)

                # Get the correct analysis method name
                if name == 'support_resistance': method_name = 'get_comprehensive_sr_analysis'
                elif name == 'patterns': method_name = 'get_comprehensive_patterns_analysis'
                else: method_name = f'get_comprehensive_{name}_analysis'

                self.analysis_results[name] = getattr(instance, method_name)()
            except Exception as e:
                self.analysis_results[name] = {'error': str(e), 'total_score': 0, 'sr_score': 0, 'fib_score': 0, 'pattern_score': 0}

    def run_trade_management_analysis(self):
        try:
            tm = TradeManagement(self.df, self.config['trading']['ACCOUNT_BALANCE'])
            self.analysis_results['trade_management'] = tm.get_comprehensive_trade_plan(self.final_recommendation, self.analysis_results)
        except Exception as e: self.analysis_results['trade_management'] = {'error': str(e)}

    def calculate_final_recommendation(self):
        scores = { 'indicators': self.analysis_results.get('indicators', {}).get('total_score', 0), 'trends': self.analysis_results.get('trends', {}).get('total_score', 0), 'channels': self.analysis_results.get('channels', {}).get('total_score', 0), 'support_resistance': self.analysis_results.get('support_resistance', {}).get('sr_score', 0), 'fibonacci': self.analysis_results.get('fibonacci', {}).get('fib_score', 0), 'patterns': self.analysis_results.get('patterns', {}).get('pattern_score', 0) }
        weights = { 'indicators': 1.5, 'trends': 3.0, 'channels': 1.0, 'support_resistance': 2.0, 'fibonacci': 1.0, 'patterns': 3.0 }
        total_score = sum(scores[key] * weights[key] for key in scores)

        if total_score >= 20: main_action, confidence = "شراء قوي 🚀", 95
        elif total_score >= 10: main_action, confidence = "شراء 📈", 85
        elif total_score >= -5: main_action, confidence = "انتظار ⏳", 60
        elif total_score >= -15: main_action, confidence = "بيع 📉", 85
        else: main_action, confidence = "بيع قوي 🔻", 95

        okx_symbol = self.symbol.replace('/', '-')
        live_price_data = self.okx_fetcher.get_cached_price(okx_symbol)
        current_price = live_price_data['price'] if live_price_data else self.df['Close'].iloc[-1] if 'Close' in self.df.columns else self.df['close'].iloc[-1]

        self.final_recommendation = { 'symbol': self.symbol, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'current_price': current_price, 'main_action': main_action, 'confidence': confidence, 'total_score': total_score, 'individual_scores': scores }

    def run_complete_analysis(self):
        """
        Runs the full analysis pipeline for the configured symbol and timeframe.
        """
        print(f"🚀 Running analysis for {self.symbol}...")
        if not self.fetch_data():
            raise ConnectionError(f"Failed to fetch data for {self.symbol}")

        # Prepare the data with all indicators
        self._prepare_data_with_indicators()

        # Run all analysis modules on the prepared data
        self.run_all_analyses()
        self.calculate_final_recommendation()
        self.run_trade_management_analysis()
        print(f"✅ Analysis complete for {self.symbol}.")
