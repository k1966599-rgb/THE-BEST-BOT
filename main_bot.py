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

warnings.filterwarnings('ignore')

class ComprehensiveTradingBot:
    """
    This class is the core analysis engine. It runs all analysis modules
    for a SINGLE symbol and a SINGLE timeframe.
    """
    def __init__(self, symbol: str, config: dict):
        self.symbol = symbol.upper()
        self.config = config
        self.df = None
        self.analysis_results = {}
        self.final_recommendation = {}
        exchange_id = config['trading']['EXCHANGE_ID']
        exchange_config = {
            'apiKey': config['exchange'].get('API_KEY'),
            'secret': config['exchange'].get('API_SECRET'),
            'password': config['exchange'].get('PASSWORD'),
            'enableRateLimit': True,
        }
        self.exchange = getattr(ccxt, exchange_id)(exchange_config)
        if config['exchange'].get('SANDBOX_MODE'): self.exchange.set_sandbox_mode(True)
        try:
            self.exchange.load_markets()
        except ccxt.BaseError as e:
            # It's better to not crash the whole app if markets fail to load,
            # especially in an interactive context.
            print(f"Warning: Could not load markets for {exchange_id}. {e}")
            pass

    def fetch_data(self) -> bool:
        timeframe = self.config['trading']['INTERVAL']
        period_str = self.config['trading']['PERIOD']
        now = datetime.utcnow()
        num = int(period_str.rstrip('ymod '))
        unit = ''.join(filter(str.isalpha, period_str))
        if unit == 'y': days = num * 365
        elif unit == 'mo': days = num * 30
        else: days = num
        since = self.exchange.parse8601((now - timedelta(days=days)).isoformat())
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, timeframe, since, limit=1000)
            if not ohlcv: return False
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            self.df = df.dropna()
            return True
        except Exception as e:
            print(f"Error fetching data for {self.symbol} on {timeframe}: {e}")
            return False

    def run_all_analyses(self):
        modules = {
            'indicators': TechnicalIndicators,
            'trends': TrendAnalysis,
            'channels': PriceChannels,
            'support_resistance': SupportResistanceAnalysis,
            'fibonacci': FibonacciAnalysis,
            'patterns': ClassicPatterns
        }
        for name, module_class in modules.items():
            try:
                # Note: The comprehensive analysis method name is slightly different for some modules
                if name == 'support_resistance':
                    method_name = 'get_comprehensive_sr_analysis'
                else:
                    method_name = f'get_comprehensive_{name}_analysis'

                instance = module_class(self.df)
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
        self.final_recommendation = {'symbol': self.symbol, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'current_price': self.df['close'].iloc[-1], 'main_action': main_action, 'confidence': confidence, 'total_score': total_score, 'individual_scores': scores}

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
