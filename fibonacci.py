import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class FibonacciAnalysis:
    """
    وحدة تحليل فيبوناتشي المتقدمة
    """
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.lookback_period = config.get('FIB_LOOKBACK', 90)
        self.data = self.df.tail(lookback_period)
        self.current_price = self.data['close'].iloc[-1] if not self.data.empty else 0
        self.retracement_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.extension_ratios = [1.272, 1.618, 2.0, 2.618]

    def find_major_swing(self) -> Dict:
        if len(self.data) < 2: return {}
        major_high_price = self.data['high'].max()
        major_low_price = self.data['low'].min()
        major_high_time = self.data['high'].idxmax()
        major_low_time = self.data['low'].idxmin()
        return {'high': {'price': major_high_price, 'time': major_high_time}, 'low': {'price': major_low_price, 'time': major_low_time}}

    def get_comprehensive_fibonacci_analysis(self) -> Dict:
        if len(self.data) < 20: # Need at least some data to find a swing
            return {'error': 'Not enough data for Fibonacci analysis.', 'fib_score': 0}

        swing = self.find_major_swing()
        if not swing:
            return {'error': 'Could not determine swing points.', 'fib_score': 0}

        high, low = swing['high'], swing['low']
        price_range = high['price'] - low['price']
        if price_range == 0:
            return {'error': 'Price range is zero.', 'fib_score': 0}

        retracements, extensions = [], []

        if high['time'] > low['time']: # Uptrend swing
            for ratio in self.retracement_ratios: retracements.append({'level': f"{ratio*100:.1f}%", 'price': high['price'] - price_range * ratio})
            for ratio in self.extension_ratios: extensions.append({'level': f"{ratio*100:.1f}%", 'price': high['price'] + price_range * (ratio - 1)})
        else: # Downtrend swing
            for ratio in self.retracement_ratios: retracements.append({'level': f"{ratio*100:.1f}%", 'price': low['price'] + price_range * ratio})
            for ratio in self.extension_ratios: extensions.append({'level': f"{ratio*100:.1f}%", 'price': low['price'] - price_range * (ratio - 1)})

        fib_score = 0
        for r in retracements:
            if abs(self.current_price - r['price']) / self.current_price < 0.02:
                fib_score += 2 if r['level'] in ['38.2%', '61.8%'] else 1

        return {'retracement_levels': retracements, 'extension_levels': extensions, 'fib_score': fib_score}
