import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class FibonacciAnalysis:
    """
    وحدة تحليل فيبوناتشي المتقدمة
    تحدد مستويات التصحيح والامتداد بناءً على الاتجاه الحالي.
    """
    def __init__(self, df: pd.DataFrame, lookback_period: int = 90):
        self.df = df.copy()
        self.data = self.df.tail(lookback_period)
        self.current_price = self.data['close'].iloc[-1]
        self.retracement_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.extension_ratios = [1.272, 1.618, 2.0, 2.618]

    def find_major_swing(self) -> Dict:
        """Finds the most recent major swing high and low."""
        if len(self.data) < 2:
            return {}

        major_high_price = self.data['high'].max()
        major_low_price = self.data['low'].min()
        major_high_time = self.data['high'].idxmax()
        major_low_time = self.data['low'].idxmin()

        return {
            'high': {'price': major_high_price, 'time': major_high_time},
            'low': {'price': major_low_price, 'time': major_low_time}
        }

    def get_comprehensive_fibonacci_analysis(self) -> Dict:
        swing = self.find_major_swing()
        if not swing:
            return {'error': 'Not enough data for Fibonacci analysis.'}

        high, low = swing['high'], swing['low']
        price_range = high['price'] - low['price']

        retracements = []
        extensions = []

        # Determine primary trend within the lookback period
        if high['time'] > low['time']: # Uptrend swing
            # Retracement levels are potential supports
            for ratio in self.retracement_ratios:
                price = high['price'] - price_range * ratio
                retracements.append({'level': f"{ratio*100:.1f}%", 'price': price})
            # Extension levels are potential targets
            for ratio in self.extension_ratios:
                price = high['price'] + price_range * (ratio - 1)
                extensions.append({'level': f"{ratio*100:.1f}%", 'price': price})
        else: # Downtrend swing
            # Retracement levels are potential resistances
            for ratio in self.retracement_ratios:
                price = low['price'] + price_range * ratio
                retracements.append({'level': f"{ratio*100:.1f}%", 'price': price})
            # Extension levels are potential targets
            for ratio in self.extension_ratios:
                price = low['price'] - price_range * (ratio - 1)
                extensions.append({'level': f"{ratio*100:.1f}%", 'price': price})

        # Simple scoring based on proximity to key levels
        fib_score = 0
        for r in retracements:
            if abs(self.current_price - r['price']) / self.current_price < 0.02: # Within 2%
                if r['level'] in ['38.2%', '61.8%']:
                    fib_score += 2
                else:
                    fib_score += 1

        return {
            'retracement_levels': retracements,
            'extension_levels': extensions,
            'fib_score': fib_score
        }
