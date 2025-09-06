import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy.signal import find_peaks

class FibonacciAnalysis:
    """
    وحدة تحليل فيبوناتشي المتقدمة
    """
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.lookback_period = config.get('FIB_LOOKBACK', 90)
        self.data = self.df.tail(self.lookback_period).reset_index(drop=True)
        self.current_price = self.data['close'].iloc[-1] if not self.data.empty else 0
        self.retracement_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.extension_ratios = [1.272, 1.618, 2.0, 2.618]

    def find_major_swing(self) -> Dict:
        """
        Finds the most recent significant price swing using pivots.
        This is more robust than finding the absolute min/max.
        """
        if len(self.data) < 20: return {}

        # 1. Find all pivot points
        prominence = self.data['close'].std() * 0.8
        if np.isnan(prominence) or prominence == 0: return {}

        high_pivots_idx, _ = find_peaks(self.data['high'], prominence=prominence, distance=5)
        low_pivots_idx, _ = find_peaks(-self.data['low'], prominence=prominence, distance=5)

        if high_pivots_idx.size < 1 or low_pivots_idx.size < 1:
            return {} # Not enough pivots

        # 2. Determine the most recent swing direction
        last_high_idx = high_pivots_idx[-1]
        last_low_idx = low_pivots_idx[-1]

        if last_high_idx > last_low_idx:
            # Recent trend is up, swing is from a low to a high
            swing_high_idx = last_high_idx
            # Find the most recent low pivot before this high
            preceding_lows = low_pivots_idx[low_pivots_idx < swing_high_idx]
            if preceding_lows.size == 0: return {}
            swing_low_idx = preceding_lows[-1]
        else:
            # Recent trend is down, swing is from a high to a low
            swing_low_idx = last_low_idx
            # Find the most recent high pivot before this low
            preceding_highs = high_pivots_idx[high_pivots_idx < swing_low_idx]
            if preceding_highs.size == 0: return {}
            swing_high_idx = preceding_highs[-1]

        swing_high_price = self.data['high'].iloc[swing_high_idx]
        swing_low_price = self.data['low'].iloc[swing_low_idx]

        # Using index for time now, which is more robust
        return {
            'high': {'price': swing_high_price, 'time': swing_high_idx},
            'low': {'price': swing_low_price, 'time': swing_low_idx}
        }

    def get_comprehensive_fibonacci_analysis(self) -> Dict:
        if len(self.data) < 20:
            return {'error': 'Not enough data for Fibonacci analysis.', 'fib_score': 0}

        swing = self.find_major_swing()
        if not swing:
            # Fallback to simple min/max if pivot method fails
            major_high_price = self.data['high'].max()
            major_low_price = self.data['low'].min()
            major_high_time = self.data['high'].idxmax()
            major_low_time = self.data['low'].idxmin()
            swing = {'high': {'price': major_high_price, 'time': major_high_time}, 'low': {'price': major_low_price, 'time': major_low_time}}

        if not swing:
            return {'error': 'Could not determine swing points.', 'fib_score': 0}

        high, low = swing['high'], swing['low']
        price_range = high['price'] - low['price']
        if price_range <= 0:
            return {'error': 'Price range is zero or invalid.', 'fib_score': 0}

        retracements, extensions = [], []

        # The logic for determining trend direction is now based on the index of the pivots
        if high['time'] > low['time']: # Uptrend swing (low came first)
            for ratio in self.retracement_ratios: retracements.append({'level': f"{ratio*100:.1f}%", 'price': high['price'] - price_range * ratio})
            for ratio in self.extension_ratios: extensions.append({'level': f"{ratio*100:.1f}%", 'price': high['price'] + price_range * (ratio - 1)})
        else: # Downtrend swing (high came first)
            for ratio in self.retracement_ratios: retracements.append({'level': f"{ratio*100:.1f}%", 'price': low['price'] + price_range * ratio})
            for ratio in self.extension_ratios: extensions.append({'level': f"{ratio*100:.1f}%", 'price': low['price'] - price_range * (ratio - 1)})

        fib_score = 0
        for r in retracements:
            # Check if current price is near a key fib level
            if abs(self.current_price - r['price']) / self.current_price < 0.015: # Tighter tolerance
                if r['level'] in ['38.2%', '50.0%', '61.8%']:
                    fib_score += 2 # Higher score for key levels
                else:
                    fib_score += 1

        return {'retracement_levels': retracements, 'extension_levels': extensions, 'fib_score': fib_score}
