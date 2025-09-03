import pandas as pd
import ccxt
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List

# --- استيراد وحدات التحليل الحقيقية ---
from indicators import TechnicalIndicators
from trends import TrendAnalysis
from channels import PriceChannels
from support_resistance import SupportResistanceAnalysis
from fibonacci import FibonacciAnalysis
from classic_patterns import ClassicPatterns

# --- الفئات الوهمية للوحدات المتبقية ---
class TradeManagement:
    def __init__(self, df, balance): self.df, self.balance = df, balance
    def get_comprehensive_trade_plan(self, results): return {'error': 'Not implemented yet'}
# --- نهاية الفئات الوهمية ---

warnings.filterwarnings('ignore')

class ComprehensiveTradingBot:
    """البوت الشامل للتحليل الفني والتداول باستخدام CCXT"""

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

        if not hasattr(ccxt, exchange_id):
            raise ValueError(f"المنصة '{exchange_id}' غير مدعومة من ccxt.")

        self.exchange = getattr(ccxt, exchange_id)(exchange_config)

        if config['exchange'].get('SANDBOX_MODE'):
            self.exchange.set_sandbox_mode(True)

        try:
            self.exchange.load_markets()
        except ccxt.BaseError as e:
            print(f"❌ فشل في تحميل الأسواق من {exchange_id}: {e}")
            raise

    def fetch_data(self) -> bool:
        timeframe = self.config['trading']['INTERVAL']
        period_str = self.config['trading']['PERIOD']
        now = datetime.utcnow()
        num = int(period_str[:-1]); unit = period_str[-1]
        if unit == 'y': days = num * 365
        elif unit == 'm': days = num * 30
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
            print(f"Error fetching data: {e}")
            return False

    def run_technical_indicators_analysis(self):
        try: self.analysis_results['indicators'] = TechnicalIndicators(self.df).get_comprehensive_analysis()
        except Exception as e: self.analysis_results['indicators'] = {'error': str(e), 'total_score': 0}

    def run_trends_analysis(self):
        try: self.analysis_results['trends'] = TrendAnalysis(self.df).get_comprehensive_trend_analysis()
        except Exception as e: self.analysis_results['trends'] = {'error': str(e), 'total_score': 0}

    def run_channels_analysis(self):
        try: self.analysis_results['channels'] = PriceChannels(self.df).get_comprehensive_channel_analysis()
        except Exception as e: self.analysis_results['channels'] = {'error': str(e), 'total_score': 0}

    def run_support_resistance_analysis(self):
        try: self.analysis_results['support_resistance'] = SupportResistanceAnalysis(self.df).get_comprehensive_sr_analysis()
        except Exception as e: self.analysis_results['support_resistance'] = {'error': str(e), 'sr_score': 0}

    def run_fibonacci_analysis(self):
        print("🔄 تحليل فيبوناتشي...")
        try:
            fib = FibonacciAnalysis(self.df)
            self.analysis_results['fibonacci'] = fib.get_comprehensive_fibonacci_analysis()
            print("✅ تم تحليل فيبوناتشي")
        except Exception as e:
            self.analysis_results['fibonacci'] = {'error': str(e), 'fib_score': 0}

    def run_classic_patterns_analysis(self):
        print("🔄 تحليل النماذج الكلاسيكية...")
        try:
            patterns = ClassicPatterns(self.df)
            self.analysis_results['patterns'] = patterns.get_comprehensive_pattern_analysis()
            print("✅ تم تحليل النماذج الكلاسيكية")
        except Exception as e:
            self.analysis_results['patterns'] = {'error': str(e), 'pattern_score': 0}

    def calculate_final_recommendation(self):
        print("🔄 حساب التوصية النهائية...")
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

        self.final_recommendation = {
            'symbol': self.symbol, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': self.df['close'].iloc[-1], 'main_action': main_action,
            'confidence': confidence, 'total_score': total_score,
            'individual_scores': scores
        }

    def generate_detailed_report(self) -> str:
        rec = self.final_recommendation
        report = f"تحليل شامل للرمز {rec.get('symbol', 'N/A')} - السعر الحالي: ${rec.get('current_price', 0):.4f}\n"
        report += f"🎯 التوصية: {rec.get('main_action', 'N/A')} (الثقة: {rec.get('confidence', 0)}%)\n"
        report += f"⚖️ النتيجة الإجمالية: {rec.get('total_score', 0)}\n"
        report += "--------------------------------\n"
        for name, score in rec.get('individual_scores', {}).items():
            report += f"- {name.title()}: {score}\n"
        return report

    def run_complete_analysis(self) -> str:
        print(f"🚀 بدء التحليل الشامل لـ {self.symbol}...")
        if not self.fetch_data():
            return f"❌ فشل في جلب البيانات لـ {self.symbol}"

        print("--- بدء وحدات التحليل ---")
        self.run_technical_indicators_analysis()
        self.run_trends_analysis()
        self.run_channels_analysis()
        self.run_support_resistance_analysis()
        self.run_fibonacci_analysis()
        self.run_classic_patterns_analysis()
        print("--- انتهاء وحدات التحليل ---")

        self.calculate_final_recommendation()
        report = self.generate_detailed_report()

        print(report)
        print("="*50)
        return report
