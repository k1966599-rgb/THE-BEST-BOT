import pandas as pd
import ccxt
from datetime import datetime, timedelta
import json
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
    # ... (init, fetch_data, get_top_usdt_coins methods remain the same)
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

    def get_top_usdt_coins(self, top_n: int = 20) -> List[str]:
        print(f"🔄 جاري جلب أفضل {top_n} عملة من {self.exchange.id}...")
        try:
            if not self.exchange.has['fetchTickers']: return []
            tickers = self.exchange.fetch_tickers()
            usdt_tickers = {s: t for s, t in tickers.items() if isinstance(t, dict) and s.endswith('/USDT') and t.get('quoteVolume') is not None and t.get('quoteVolume') > 10000000}
            sorted_tickers = sorted(usdt_tickers.values(), key=lambda x: x['quoteVolume'], reverse=True)
            return [t['symbol'] for t in sorted_tickers[:top_n]]
        except ccxt.BaseError as e:
            print(f"❌ خطأ في جلب قائمة العملات: {e}")
            return []

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
            print(f"Error fetching data for {self.symbol}: {e}")
            return False

    def run_all_analyses(self):
        # ... (this method remains the same)
        analysis_functions = [
            self.run_technical_indicators_analysis, self.run_trends_analysis,
            self.run_channels_analysis, self.run_support_resistance_analysis,
            self.run_fibonacci_analysis, self.run_classic_patterns_analysis
        ]
        print("--- بدء وحدات التحليل ---")
        for func in analysis_functions:
            print(f"🔄 Executing: {func.__name__}...")
            func()
        print("--- انتهاء وحدات التحليل ---")

    # ... (all run_..._analysis methods remain the same)
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
        except Exception as e: self.analysis_results['trade_management'] = {'error': str(e)}

    def calculate_final_recommendation(self):
        # ... (this method remains the same)
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

    def generate_detailed_report(self) -> str:
        """Generates the final report based on the user's detailed template."""
        rec = self.final_recommendation
        sr = self.analysis_results.get('support_resistance', {})
        trade_plan = self.analysis_results.get('trade_management', {})
        indicators = self.analysis_results.get('indicators', {})

        # Helper for formatting zones
        def format_zone(zone_data, current_price):
            if not zone_data: return "غير محدد"
            start, end = zone_data['start'], zone_data['end']
            distance = abs(current_price - zone_data['avg_price'])
            return (f"📍 **السعر:** ${start:,.2f} - ${end:,.2f}\n"
                    f"- **المسافة:** {distance:,.0f} نقطة\n"
                    f"- **قوة المنطقة:** {zone_data.get('strength', 'N/A')} (تم اختبارها {zone_data.get('touches', 'N/A')} مرات)")

        # Main Recommendation
        report = f"🪙 **تحليل فني شامل - {rec.get('symbol')} ({self.config['trading']['EXCHANGE_ID'].upper()})**\n"
        report += f"**📅 التاريخ:** {rec.get('timestamp')}\n"
        report += f"**💰 السعر الحالي:** ${rec.get('current_price', 0):,.2f}\n"
        report += "---\n"
        report += f"## 🎯 التوصية الرئيسية من الاستراتيجية\n"
        report += f"**{rec.get('main_action', 'N/A')}** | **مستوى الثقة: {rec.get('confidence', 0)}%** | **النتيجة الإجمالية: {rec.get('total_score', 0):+}**\n"
        report += "---\n"

        # Critical Zones
        report += f"## 🔥 المناطق الحرجة حسب الاستراتيجية\n"
        report += f"### 📊 الوضع الحالي للسعر\n**{rec.get('symbol')} الآن عند: ${rec.get('current_price', 0):,.2f}**\n\n"

        supply_zone = sr.get('primary_supply_zone')
        demand_zone = sr.get('primary_demand_zone')

        report += f"### 🔴 منطقة العرض (Supply Zone) - مقاومة قوية\n{format_zone(supply_zone, rec.get('current_price', 0))}\n\n"
        report += f"### 🟢 منطقة الطلب (Demand Zone) - دعم قوي\n{format_zone(demand_zone, rec.get('current_price', 0))}\n"
        report += "---\n"

        # Trading Plan
        report += f"## 🎯 خطة التداول المبنية على الاستراتيجية\n"
        if 'entry_price' in trade_plan:
            rr_ratio = trade_plan.get('risk_reward_ratio', 0)
            report += f"### 🟢 سيناريو {trade_plan.get('direction', '')} الأساسي\n"
            report += f"**نقطة الدخول:** ${trade_plan.get('entry_price', 0):,.2f}\n"
            report += f"- **وقف الخسارة:** ${trade_plan.get('stop_loss', 0):,.2f}\n"
            report += f"- **الهدف:** ${trade_plan.get('profit_target', 0):,.2f}\n"
            report += f"- **نسبة المخاطرة/العائد:** 1:{rr_ratio:.1f}\n"
        else:
            report += "لا توجد خطة تداول واضحة حاليًا.\n"
        report += "---\n"

        # Indicator Analysis
        report += f"## 🔍 تحليل المؤشرات داخل المناطق\n"
        if 'error' not in indicators:
            rsi = indicators.get('momentum', {}).get('rsi', 0)
            macd = indicators.get('momentum', {}).get('macd', 0)
            macd_signal = indicators.get('momentum', {}).get('macd_signal', 0)
            report += f"### 📊 القوة النسبية (RSI = {rsi:.1f})\n"
            report += f"- **الوضع:** {'ذروة شراء' if rsi > 70 else 'ذروة بيع' if rsi < 30 else 'متوسط صحي'}\n"
            report += f"### 📈 MACD والزخم\n"
            report += f"- **الإشارة:** {'شراء' if macd > macd_signal else 'بيع'}\n"

        report += "---\n"
        report += "*📝 التحليل مبني على الاستراتيجية الشاملة - ليس نصيحة استثمارية*"

        return report

    def run_complete_analysis(self) -> str:
        print(f"🚀 بدء التحليل الشامل لـ {self.symbol}...")
        if not self.fetch_data(): return f"❌ فشل في جلب البيانات لـ {self.symbol}"
        self.run_all_analyses()
        self.calculate_final_recommendation()
        self.run_trade_management_analysis()
        report = self.generate_detailed_report()
        return report
