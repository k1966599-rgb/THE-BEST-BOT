import pandas as pd
import ccxt
from datetime import datetime, timedelta
import warnings
from typing import Dict, List

from analysis.technical_score import TechnicalIndicators
from analysis.trends import TrendAnalysis
from analysis.trend_lines import TrendLineAnalysis
from analysis.channels import PriceChannels
from analysis.support_resistance import SupportResistanceAnalysis
from analysis.fibonacci import FibonacciAnalysis
from analysis.classic_patterns import ClassicPatterns
from trade_management import TradeManagement
from okx_data import OKXDataFetcher
from indicators import apply_all_indicators

warnings.filterwarnings('ignore')

class ComprehensiveTradingBot:
    def __init__(self, symbol: str, timeframe: str, config: dict, okx_fetcher: OKXDataFetcher):
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.config = config
        self.okx_fetcher = okx_fetcher
        self.df = None
        self.df_with_indicators = None
        self.analysis_results = {}
        self.final_recommendation = {}

    def _get_max_lookback_days(self) -> int:
        """
        Calculates the maximum lookback period in days required by any analysis module
        for the current timeframe.
        """
        analysis_config = self.config.get('analysis', {})
        overrides = analysis_config.get('TIMEFRAME_OVERRIDES', {}).get(self.timeframe, {})

        # Get all lookback values from the config, using overrides if they exist
        lookbacks = [
            overrides.get('SR_LOOKBACK', analysis_config.get('SR_LOOKBACK', 100)),
            overrides.get('FIB_LOOKBACK', analysis_config.get('FIB_LOOKBACK', 90)),
            overrides.get('PATTERN_LOOKBACK', analysis_config.get('PATTERN_LOOKBACK', 90)),
            overrides.get('CHANNEL_LOOKBACK', analysis_config.get('CHANNEL_LOOKBACK', 50)),
            analysis_config.get('TREND_LONG_PERIOD', 100) # Trend analysis also has a lookback
        ]

        max_lookback_candles = max(lookbacks)

        # Convert max lookback in candles to days
        # This is an approximation, but it's better than a fixed period
        timeframe_char = self.timeframe[-1]
        timeframe_val = int(self.timeframe[:-1])

        if timeframe_char == 'm':
            candles_per_day = 24 * 60 / timeframe_val
        elif timeframe_char == 'h':
            candles_per_day = 24 / timeframe_val
        elif timeframe_char == 'd':
            candles_per_day = 1
        else: # Default for weekly, etc.
            candles_per_day = 1.0/7.0

        # Add a buffer of 10%
        required_days = (max_lookback_candles / candles_per_day) * 1.1

        # Return integer number of days, with a minimum of 30
        calculated_days = max(30, int(required_days))
        print(f"DEBUG: For timeframe {self.timeframe}, max lookback is {max_lookback_candles} candles, calculated days to fetch: {calculated_days}")
        return calculated_days

    def fetch_data(self) -> bool:
        okx_symbol = self.symbol.replace('/', '-')
        api_timeframe = self.timeframe.replace('d', 'D').replace('h', 'H')

        days_to_fetch = self._get_max_lookback_days()

        print(f"Fetching historical data for {okx_symbol} on timeframe {api_timeframe} ({days_to_fetch} days) via OKXDataFetcher...")

        historical_data = self.okx_fetcher.fetch_historical_data(symbol=okx_symbol, timeframe=api_timeframe, days_to_fetch=days_to_fetch)

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
        Calculates all necessary technical indicators once by calling the refactored indicator modules.
        """
        if self.df is None: return

        # Create a copy to hold the indicators
        self.df_with_indicators = self.df.copy()
        # Rename columns for compatibility with indicator calculations
        self.df_with_indicators.rename(columns={"high": "High", "low": "Low", "open": "Open", "close": "Close", "volume": "Volume"}, inplace=True, errors='ignore')

        # Apply all indicators from the new modular structure
        self.df_with_indicators = apply_all_indicators(self.df_with_indicators)

    def run_all_analyses(self):
        # Ensure we have the dataframe with indicators before running analyses
        if self.df_with_indicators is None:
            self.analysis_results = {'error': "Indicator dataframe not prepared."}
            return

        modules = {
            'indicators': (TechnicalIndicators, 'get_comprehensive_analysis'),
            'trends': (TrendAnalysis, 'get_comprehensive_trends_analysis'),
            'trend_lines': (TrendLineAnalysis, 'get_comprehensive_trend_lines_analysis'),
            'channels': (PriceChannels, 'get_comprehensive_channels_analysis'),
            'support_resistance': (SupportResistanceAnalysis, 'get_comprehensive_sr_analysis'),
            'fibonacci': (FibonacciAnalysis, 'get_comprehensive_fibonacci_analysis'),
            'patterns': (ClassicPatterns, 'get_comprehensive_patterns_analysis')
        }
        analysis_config = self.config.get('analysis', {})
        for name, (module_class, method_name) in modules.items():
            try:
                # Pass the timeframe to the constructor of the analysis modules
                instance = module_class(self.df_with_indicators, config=analysis_config, timeframe=self.timeframe)
                self.analysis_results[name] = getattr(instance, method_name)()
            except Exception as e:
                self.analysis_results[name] = {'error': str(e)}

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

        self.final_recommendation = {
            'symbol': self.symbol,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': current_price,
            'main_action': main_action,
            'confidence': confidence,
            'total_score': total_score,
            'individual_scores': scores,
            'trend_line_analysis': self.analysis_results.get('trend_lines', {})
        }

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
