import pandas as pd
import ccxt
from datetime import datetime, timedelta
import json
import warnings
from typing import Dict, List

# --- استيراد جميع وحدات التحليل ---
from indicators import TechnicalIndicators
from trends import TrendAnalysis
from channels import PriceChannels
from support_resistance import SupportResistanceAnalysis
from fibonacci import FibonacciAnalysis
from classic_patterns import ClassicPatterns
from trade_management import TradeManagement

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

        self.exchange = getattr(ccxt, exchange_id)(exchange_config)
        if config['exchange'].get('SANDBOX_MODE'): self.exchange.set_sandbox_mode(True)
        self.exchange.load_markets()

    def fetch_data(self) -> bool:
        timeframe = self.config['trading']['INTERVAL']
        period_str = self.config['trading']['PERIOD']
        now = datetime.utcnow()
        num = int(period_str.rstrip('ymo d'))
        unit = period_str[-1]
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
            print(f"Error fetching data for {self.symbol}: {e}")
            return False

    def run_all_analyses(self):
        analysis_functions = [
            self.run_technical_indicators_analysis, self.run_trends_analysis,
            self.run_channels_analysis, self.run_support_resistance_analysis,
            self.run_fibonacci_analysis, self.run_classic_patterns_analysis
        ]
        for func in analysis_functions:
            func()

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
        try: self.analysis_results['fibonacci'] = FibonacciAnalysis(self.df).get_comprehensive_fibonacci_analysis()
        except Exception as e: self.analysis_results['fibonacci'] = {'error': str(e), 'fib_score': 0}

    def run_classic_patterns_analysis(self):
        try: self.analysis_results['patterns'] = ClassicPatterns(self.df).get_comprehensive_pattern_analysis()
        except Exception as e: self.analysis_results['patterns'] = {'error': str(e), 'pattern_score': 0}

    def run_trade_management_analysis(self):
        try:
            tm = TradeManagement(self.df, self.config['trading']['ACCOUNT_BALANCE'])
            self.analysis_results['trade_management'] = tm.get_comprehensive_trade_plan(self.final_recommendation, self.analysis_results)
        except Exception as e:
            self.analysis_results['trade_management'] = {'error': str(e)}

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

        self.final_recommendation = {
            'symbol': self.symbol, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': self.df['close'].iloc[-1], 'main_action': main_action,
            'confidence': confidence, 'total_score': total_score,
            'individual_scores': scores
        }

    def generate_detailed_report(self) -> str:
        rec = self.final_recommendation
        trade_plan = self.analysis_results.get('trade_management', {})

        report = f"تحليل شامل لـ {rec.get('symbol')} | السعر الحالي: ${rec.get('current_price', 0):.4f}\n"
        report += f"=================================================\n"
        report += f"🎯 التوصية النهائية: {rec.get('main_action', 'N/A')} (الثقة: {rec.get('confidence', 0)}%)\n"
        report += f"⚖️ النتيجة الإجمالية: {rec.get('total_score', 0)}\n\n"

        report += "--- تفاصيل النتائج ---\n"
        for name, score in rec.get('individual_scores', {}).items():
            report += f"- {name.replace('_', ' ').title()}: {score}\n"

        if 'error' not in trade_plan:
            report += "\n--- خطة التداول المقترحة ---\n"
            report += f"الإشارة: {trade_plan.get('signal', 'N/A')}\n"
            if 'entry_price' in trade_plan:
                report += f"سعر الدخول: ${trade_plan.get('entry_price', 0):.4f}\n"
                report += f"وقف الخسارة: ${trade_plan.get('stop_loss', 0):.4f}\n"
                report += f"جني الأرباح: ${trade_plan.get('profit_target', 0):.4f}\n"
                report += f"نسبة المخاطرة/العائد: {trade_plan.get('risk_reward_ratio', 0):.2f}\n"

        return report

    def run_complete_analysis(self) -> str:
        print(f"🚀 بدء التحليل الشامل لـ {self.symbol}...")
        if not self.fetch_data():
            return f"❌ فشل في جلب البيانات لـ {self.symbol}"

        self.run_all_analyses()
        self.calculate_final_recommendation()
        self.run_trade_management_analysis() # Run after final recommendation

        report = self.generate_detailed_report()

        print(report)
        return report
