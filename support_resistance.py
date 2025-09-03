import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

class SupportResistanceAnalysis:
    """وحدة تحليل الدعوم والمقاومة الشاملة"""

    def __init__(self, df: pd.DataFrame, lookback_period: int = 100, tolerance: float = 0.005):
        self.df = df.copy()
        self.lookback_period = lookback_period
        self.tolerance = tolerance
        self.levels = {'support': [], 'resistance': []}

    def identify_pivot_points(self, window: int = 5) -> Dict[str, List]:
        """تحديد النقاط المحورية (Pivot Points)"""
        pivot_highs, pivot_lows = [], []
        data = self.df.tail(self.lookback_period)

        if len(data) <= window * 2:
            return {'pivot_highs': [], 'pivot_lows': []}

        for i in range(window, len(data) - window):
            is_pivot_high = data['high'].iloc[i] == data['high'].iloc[i-window:i+window+1].max()
            if is_pivot_high:
                pivot_highs.append({'price': data['high'].iloc[i], 'touches': 1})

            is_pivot_low = data['low'].iloc[i] == data['low'].iloc[i-window:i+window+1].min()
            if is_pivot_low:
                pivot_lows.append({'price': data['low'].iloc[i], 'touches': 1})

        return {'pivot_highs': pivot_highs, 'pivot_lows': pivot_lows}

    def cluster_levels(self, points: List[Dict], level_type: str) -> List[Dict]:
        """تجميع المستويات المتقاربة"""
        if not points: return []

        sorted_points = sorted(points, key=lambda x: x['price'])
        clusters = []

        if not sorted_points: return []

        current_cluster = [sorted_points[0]]
        for i in range(1, len(sorted_points)):
            price_diff = abs(sorted_points[i]['price'] - current_cluster[-1]['price']) / current_cluster[-1]['price']
            if price_diff <= self.tolerance:
                current_cluster.append(sorted_points[i])
            else:
                avg_price = np.mean([p['price'] for p in current_cluster])
                touches = sum([p['touches'] for p in current_cluster])
                clusters.append({'price': avg_price, 'touches': touches, 'strength': touches})
                current_cluster = [sorted_points[i]]

        if current_cluster:
            avg_price = np.mean([p['price'] for p in current_cluster])
            touches = sum([p['touches'] for p in current_cluster])
            clusters.append({'price': avg_price, 'touches': touches, 'strength': touches})

        return clusters

    def calculate_volume_profile(self) -> List[Dict]:
        """حساب ملف الحجم لتحديد مستويات الدعم والمقاومة"""
        if 'volume' not in self.df.columns or self.df['volume'].sum() == 0:
            return []

        data = self.df.tail(self.lookback_period)
        price_range = np.linspace(data['low'].min(), data['high'].max(), 20)
        volume_at_price = defaultdict(float)

        for _, row in data.iterrows():
            price_center = (row['high'] + row['low']) / 2
            price_bin = np.argmin(np.abs(price_range - price_center))
            volume_at_price[price_range[price_bin]] += row['volume']

        sorted_levels = sorted(volume_at_price.items(), key=lambda x: x[1], reverse=True)

        volume_levels = []
        for price, volume in sorted_levels[:5]: # Top 5 volume levels
            volume_levels.append({
                'price': price,
                'strength': volume / data['volume'].sum(),
                'touches': 1 # Volume profile doesn't have "touches" in the same way
            })
        return volume_levels

    def get_comprehensive_sr_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل للدعوم والمقاومة"""
        pivots = self.identify_pivot_points()

        resistance_levels = self.cluster_levels(pivots['pivot_highs'], 'resistance')
        support_levels = self.cluster_levels(pivots['pivot_lows'], 'support')

        volume_levels = self.calculate_volume_profile()

        current_price = self.df['close'].iloc[-1]

        for level in volume_levels:
            if level['price'] > current_price:
                resistance_levels.append(level)
            else:
                support_levels.append(level)

        # Sort by strength
        resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
        support_levels.sort(key=lambda x: x['strength'], reverse=True)

        nearest_support = min(support_levels, key=lambda x: abs(x['price'] - current_price)) if support_levels else None
        nearest_resistance = min(resistance_levels, key=lambda x: abs(x['price'] - current_price)) if resistance_levels else None

        sr_score = 0
        if nearest_resistance and nearest_support:
            price_position = (current_price - nearest_support['price']) / (nearest_resistance['price'] - nearest_support['price'])
            if price_position > 0.8: sr_score -= 1
            elif price_position < 0.2: sr_score += 1

        avg_support_strength = np.mean([s['strength'] for s in support_levels]) if support_levels else 0
        avg_resistance_strength = np.mean([r['strength'] for r in resistance_levels]) if resistance_levels else 0
        if avg_support_strength > avg_resistance_strength: sr_score += 1
        else: sr_score -=1

        if sr_score >= 2: recommendation = "الدعوم قوية - فرصة شراء"
        elif sr_score >= 1: recommendation = "دعم محتمل - مراقبة الشراء"
        elif sr_score <= -2: recommendation = "المقاومات قوية - فرصة بيع"
        else: recommendation = "محايد - انتظار"

        return {
            'key_resistance': resistance_levels[:3],
            'key_support': support_levels[:3],
            'nearest_resistance': nearest_resistance,
            'nearest_support': nearest_support,
            'sr_score': sr_score,
            'recommendation': recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
