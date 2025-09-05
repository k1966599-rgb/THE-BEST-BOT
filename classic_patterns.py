import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, List, Any

class ClassicPatterns:
    """
    وحدة تحليل النماذج الكلاسيكية المتقدمة
    Uses a more robust, pivot-based detection method.
    """
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.lookback_period = config.get('PATTERN_LOOKBACK', 90)
        self.data = self.df.tail(self.lookback_period)
        self.current_price = self.data['close'].iloc[-1] if not self.data.empty else 0
        self.price_tolerance = config.get('PATTERN_PRICE_TOLERANCE', 0.03)

    def get_pivots(self):
        """Finds significant high and low pivot points."""
        prominence = self.data['close'].std() * 0.8
        high_pivots_idx, _ = find_peaks(self.data['high'], prominence=prominence, distance=5)
        low_pivots_idx, _ = find_peaks(-self.data['low'], prominence=prominence, distance=5)

        highs = [{'index': i, 'price': self.data['high'].iloc[i]} for i in high_pivots_idx]
        lows = [{'index': i, 'price': self.data['low'].iloc[i]} for i in low_pivots_idx]

        return highs, lows

    def check_double_top(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        patterns = []
        if len(highs) < 2: return patterns

        h1, h2 = highs[-2], highs[-1]
        if abs(h1['price'] - h2['price']) / h1['price'] < self.price_tolerance:
            intervening_lows = [l for l in lows if l['index'] > h1['index'] and l['index'] < h2['index']]
            if intervening_lows:
                neckline = min(intervening_lows, key=lambda x: x['price'])
                status = "مكتمل ✅" if self.current_price < neckline['price'] else "في التكوين 🟡"
                patterns.append({'name': 'قمة مزدوجة (Double Top)', 'status': status, 'neckline': neckline['price']})
        return patterns

    def check_double_bottom(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        patterns = []
        if len(lows) < 2: return patterns

        l1, l2 = lows[-2], lows[-1]
        if abs(l1['price'] - l2['price']) / l1['price'] < self.price_tolerance:
            intervening_highs = [h for h in highs if h['index'] > l1['index'] and h['index'] < l2['index']]
            if intervening_highs:
                neckline = max(intervening_highs, key=lambda x: x['price'])
                status = "مكتمل ✅" if self.current_price > neckline['price'] else "في التكوين 🟡"
                patterns.append({'name': 'قاع مزدوج (Double Bottom)', 'status': status, 'neckline': neckline['price']})
        return patterns

    def check_head_and_shoulders(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        patterns = []
        if len(highs) < 3 or len(lows) < 2: return patterns

        h1, h2, h3 = highs[-3], highs[-2], highs[-1]
        if h2['price'] > h1['price'] and h2['price'] > h3['price']:
            if abs(h1['price'] - h3['price']) / h1['price'] < (self.price_tolerance * 2):
                l1 = next((l for l in lows if l['index'] > h1['index'] and l['index'] < h2['index']), None)
                l2 = next((l for l in lows if l['index'] > h2['index'] and l['index'] < h3['index']), None)
                if l1 and l2:
                    neckline_price = (l1['price'] + l2['price']) / 2
                    status = "مكتمل ✅" if self.current_price < neckline_price else "في التكوين 🟡"
                    patterns.append({'name': 'رأس وكتفين (H&S)', 'status': status, 'neckline': neckline_price})
        return patterns

    def get_comprehensive_pattern_analysis(self) -> Dict:
        if len(self.data) < self.lookback_period:
            return {'error': f'Not enough data.', 'pattern_score': 0, 'found_patterns': []}

        highs, lows = self.get_pivots()

        all_patterns = []
        all_patterns.extend(self.check_double_top(highs, lows))
        all_patterns.extend(self.check_double_bottom(highs, lows))
        all_patterns.extend(self.check_head_and_shoulders(highs, lows))

        all_patterns.sort(key=lambda x: x.get('index', self.lookback_period), reverse=True)

        pattern_score = 0
        for p in all_patterns:
            if p.get('status') == "مكتمل ✅":
                pattern_score += 2 if 'Bottom' in p['name'] or 'قاع' in p['name'] else -2
            else:
                pattern_score += 1 if 'Bottom' in p['name'] or 'قاع' in p['name'] else -1

        return {
            'found_patterns': all_patterns,
            'pattern_score': pattern_score
        }
