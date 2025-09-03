import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import warnings

warnings.filterwarnings('ignore')

class FibonacciAnalysis:
    """وحدة تحليل فيبوناتشي الشاملة"""

    def __init__(self, df: pd.DataFrame, lookback_period: int = 50):
        self.df = df.copy()
        self.lookback_period = lookback_period

        self.fib_ratios = {
            'retracement': [0.236, 0.382, 0.500, 0.618, 0.786],
            'extension': [1.272, 1.618, 2.618],
        }
        self.fib_importance = {0.236: 2, 0.382: 4, 0.500: 3, 0.618: 5, 0.786: 4, 1.272: 4, 1.618: 5, 2.618: 4}

    def find_swing_points(self) -> Dict[str, Optional[Dict]]:
        """البحث عن أهم قمة وقاع في الفترة المحددة"""
        recent_data = self.df.tail(self.lookback_period)
        if recent_data.empty:
            return {'high': None, 'low': None}

        swing_high_price = recent_data['high'].max()
        swing_low_price = recent_data['low'].min()

        swing_high_date = recent_data['high'].idxmax()
        swing_low_date = recent_data['low'].idxmin()

        return {
            'high': {'price': swing_high_price, 'date': swing_high_date},
            'low': {'price': swing_low_price, 'date': swing_low_date}
        }

    def calculate_fibonacci_retracement(self, high_point: Dict, low_point: Dict) -> Dict[str, Any]:
        """حساب مستويات فيبوناتشي للتصحيح"""
        high_price = high_point['price']
        low_price = low_point['price']
        price_range = high_price - low_price

        if price_range <= 0: return {'error': 'نطاق سعري غير صالح'}

        levels = {}
        # اتجاه صاعد (تصحيح هابط)
        for ratio in self.fib_ratios['retracement']:
            level_price = high_price - (price_range * ratio)
            levels[f'Retracement_{ratio*100:.1f}%'] = level_price

        # اتجاه هابط (تصحيح صاعد)
        for ratio in self.fib_ratios['retracement']:
            level_price = low_price + (price_range * ratio)
            levels[f'Bounce_{ratio*100:.1f}%'] = level_price

        return {'levels': levels}

    def calculate_fibonacci_extension(self, high_point: Dict, low_point: Dict) -> Dict[str, Any]:
        """حساب أهداف فيبوناتشي للامتداد"""
        high_price = high_point['price']
        low_price = low_point['price']
        price_range = high_price - low_price

        if price_range <= 0: return {'error': 'نطاق سعري غير صالح'}

        levels = {}
        # امتداد صاعد
        for ratio in self.fib_ratios['extension']:
            level_price = high_price + (price_range * (ratio - 1))
            levels[f'Extension_Up_{ratio*100:.1f}%'] = level_price

        # امتداد هابط
        for ratio in self.fib_ratios['extension']:
            level_price = low_price - (price_range * (ratio - 1))
            levels[f'Extension_Down_{ratio*100:.1f}%'] = level_price

        return {'levels': levels}

    def get_comprehensive_fibonacci_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل لفيبوناتشي"""
        swing_points = self.find_swing_points()
        high_point = swing_points.get('high')
        low_point = swing_points.get('low')

        if not high_point or not low_point:
            return {'error': 'لا يمكن تحديد نقاط التأرجح'}

        retracement = self.calculate_fibonacci_retracement(high_point, low_point)
        extension = self.calculate_fibonacci_extension(high_point, low_point)

        current_price = self.df['close'].iloc[-1]

        # تقييم المستويات
        fib_score = 0
        signals = []

        # فحص مستويات الدعم (التصحيح)
        for name, level in retracement.get('levels', {}).items():
            if 'Retracement' in name and current_price > level and (current_price - level) / current_price < 0.02:
                fib_score += 1
                signals.append(f"قرب دعم فيبوناتشي عند {level:.2f}")

        # فحص مستويات المقاومة (الارتداد)
        for name, level in retracement.get('levels', {}).items():
             if 'Bounce' in name and current_price < level and (level - current_price) / current_price < 0.02:
                fib_score -= 1
                signals.append(f"قرب مقاومة فيبوناتشي عند {level:.2f}")

        if fib_score >= 1: recommendation = "إشارة صعود محتملة من فيبوناتشي"
        elif fib_score <= -1: recommendation = "إشارة هبوط محتملة من فيبوناتشي"
        else: recommendation = "لا توجد إشارة واضحة من فيبوناتشي"

        return {
            'retracement_levels': retracement.get('levels'),
            'extension_levels': extension.get('levels'),
            'swing_high': high_point,
            'swing_low': low_point,
            'fib_score': fib_score,
            'signals': signals,
            'recommendation': recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
