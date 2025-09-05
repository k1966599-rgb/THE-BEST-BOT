import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, List, Any

class ClassicPatterns:
    """
    وحدة تحليل النماذج الكلاسيكية المتقدمة
    Uses a more robust, pivot-based detection method.
    Enhanced to detect more patterns and provide detailed analysis for reporting.
    """
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.lookback_period = config.get('PATTERN_LOOKBACK', 90)
        self.data = self.df.tail(self.lookback_period)
        self.current_price = self.data['close'].iloc[-1] if not self.data.empty else 0
        self.price_tolerance = config.get('PATTERN_PRICE_TOLERANCE', 0.03)

    def get_pivots(self, prominence_multiplier=0.8):
        """Finds significant high and low pivot points."""
        if self.data.empty: return [], []
        prominence = self.data['close'].std() * prominence_multiplier
        if np.isnan(prominence) or prominence == 0: return [], []

        high_pivots_idx, _ = find_peaks(self.data['high'], prominence=prominence, distance=5)
        low_pivots_idx, _ = find_peaks(-self.data['low'], prominence=prominence, distance=5)

        highs = [{'index': i, 'price': self.data['high'].iloc[i]} for i in high_pivots_idx]
        lows = [{'index': i, 'price': self.data['low'].iloc[i]} for i in low_pivots_idx]

        return highs, lows

    def check_ascending_triangle(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        """Detects ascending triangles."""
        patterns = []
        if len(highs) < 2 or len(lows) < 2: return patterns

        last_high = highs[-1]['price']
        resistance_highs = [h for h in highs if abs(h['price'] - last_high) / last_high < self.price_tolerance]

        if len(resistance_highs) < 2: return patterns

        resistance_line = np.mean([h['price'] for h in resistance_highs])

        trend_lows = []
        for i in range(len(lows) - 1):
            if lows[i+1]['price'] > lows[i]['price']:
                trend_lows.append(lows[i])
        if trend_lows and lows[-1]['price'] > trend_lows[-1]['price']:
             trend_lows.append(lows[-1])

        if len(trend_lows) < 2: return patterns

        if trend_lows[-1]['price'] > resistance_line: return patterns

        height = resistance_line - trend_lows[0]['price']
        patterns.append({
            'name': 'مثلث صاعد (Ascending Triangle)',
            'status': 'قيد التكوين 🟡' if self.current_price < resistance_line else 'مكتمل ✅',
            'resistance_line': resistance_line,
            'support_line_start': trend_lows[0]['price'],
            'support_line_end': trend_lows[-1]['price'],
            'calculated_target': resistance_line + height,
            'confidence': 75
        })
        return patterns

    def check_bull_flag(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        """Detects bull flags."""
        patterns = []
        if len(self.data) < 15: return patterns

        pole_start_idx = self.data['low'].idxmin()
        pole_end_idx = self.data['high'].loc[pole_start_idx:].idxmax()

        if pole_end_idx is pd.NaT or pole_start_idx is pd.NaT: return patterns

        pole_height = self.data['high'].loc[pole_end_idx] - self.data['low'].loc[pole_start_idx]
        if pole_height < self.data['close'].mean() * 0.1: return patterns

        flag_data = self.data.loc[pole_end_idx:]
        if len(flag_data) < 5: return patterns

        flag_high = flag_data['high'].max()
        flag_low = flag_data['low'].min()

        if (flag_high - flag_low) / flag_high < 0.05:
             patterns.append({
                'name': 'علم صاعد (Bull Flag)',
                'status': 'قيد التكوين 🟡' if self.current_price < flag_high else 'مكتمل ✅',
                'pole_start_price': self.data['low'].loc[pole_start_idx],
                'pole_end_price': self.data['high'].loc[pole_end_idx],
                'resistance_line': flag_high,
                'support_line': flag_low,
                'calculated_target': flag_high + pole_height,
                'confidence': 80
            })
        return patterns

    def check_double_bottom(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        """Detects double bottoms and returns detailed info."""
        patterns = []
        if len(lows) < 2: return patterns

        l1, l2 = lows[-2], lows[-1]
        if abs(l1['price'] - l2['price']) / l1['price'] < self.price_tolerance:
            intervening_highs = [h for h in highs if h['index'] > l1['index'] and h['index'] < l2['index']]
            if intervening_highs:
                neckline_high = max(intervening_highs, key=lambda x: x['price'])
                neckline_price = neckline_high['price']
                height = neckline_price - (l1['price'] + l2['price']) / 2
                patterns.append({
                    'name': 'قاع مزدوج (Double Bottom)',
                    'status': 'مكتمل ✅' if self.current_price > neckline_price else 'قيد التكوين 🟡',
                    'neckline': neckline_price,
                    'bottom_1_price': l1['price'],
                    'bottom_2_price': l2['price'],
                    'calculated_target': neckline_price + height,
                    'confidence': 65
                })
        return patterns

    def check_double_top(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        """Detects double tops and returns detailed info."""
        patterns = []
        if len(highs) < 2: return patterns

        h1, h2 = highs[-2], highs[-1]
        if abs(h1['price'] - h2['price']) / h1['price'] < self.price_tolerance:
            intervening_lows = [l for l in lows if l['index'] > h1['index'] and l['index'] < h2['index']]
            if intervening_lows:
                neckline_low = min(intervening_lows, key=lambda x: x['price'])
                neckline_price = neckline_low['price']
                height = h1['price'] - neckline_price
                patterns.append({
                    'name': 'قمة مزدوجة (Double Top)',
                    'status': 'مكتمل ✅' if self.current_price < neckline_price else 'قيد التكوين 🟡',
                    'neckline': neckline_price,
                    'top_1_price': h1['price'],
                    'top_2_price': h2['price'],
                    'calculated_target': neckline_price - height,
                    'confidence': 70
                })
        return patterns

    def check_head_and_shoulders(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        """Detects Head and Shoulders patterns."""
        patterns = []
        if len(highs) < 3 or len(lows) < 2: return patterns

        h1, h2, h3 = highs[-3], highs[-2], highs[-1] # Left Shoulder, Head, Right Shoulder
        if h2['price'] > h1['price'] and h2['price'] > h3['price']:
            if abs(h1['price'] - h3['price']) / h1['price'] < (self.price_tolerance * 2): # Shoulders are similar height
                l1 = next((l for l in lows if l['index'] > h1['index'] and l['index'] < h2['index']), None)
                l2 = next((l for l in lows if l['index'] > h2['index'] and l['index'] < h3['index']), None)
                if l1 and l2:
                    neckline_price = (l1['price'] + l2['price']) / 2
                    height = h2['price'] - neckline_price
                    patterns.append({
                        'name': 'رأس وكتفين (H&S)',
                        'status': 'مكتمل ✅' if self.current_price < neckline_price else 'قيد التكوين 🟡',
                        'neckline': neckline_price,
                        'head_price': h2['price'],
                        'left_shoulder_price': h1['price'],
                        'right_shoulder_price': h3['price'],
                        'calculated_target': neckline_price - height,
                        'confidence': 75
                    })
        return patterns

    def get_comprehensive_patterns_analysis(self) -> Dict:
        """
        Runs all pattern detection methods and returns a structured dictionary.
        """
        if len(self.data) < 20:
            return {'error': 'Not enough data.', 'pattern_score': 0, 'found_patterns': []}

        highs, lows = self.get_pivots()
        if not highs or not lows:
            return {'error': 'Could not determine pivots.', 'pattern_score': 0, 'found_patterns': []}

        all_patterns = []
        all_patterns.extend(self.check_ascending_triangle(highs, lows))
        all_patterns.extend(self.check_bull_flag(highs, lows))
        all_patterns.extend(self.check_double_bottom(highs, lows))
        all_patterns.extend(self.check_double_top(highs, lows))
        all_patterns.extend(self.check_head_and_shoulders(highs, lows))

        pattern_score = 0
        for p in all_patterns:
            score_multiplier = 1
            if 'قاع' in p['name'] or 'صاعد' in p['name']: score_multiplier = 1
            elif 'قمة' in p['name'] or 'رأس' in p['name']: score_multiplier = -1

            if p.get('status') == "مكتمل ✅": pattern_score += 2 * score_multiplier
            else: pattern_score += 1 * score_multiplier

        all_patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        return {
            'found_patterns': all_patterns,
            'pattern_score': pattern_score,
            'error': None
        }

    def get_comprehensive_pattern_analysis(self) -> Dict:
        return self.get_comprehensive_patterns_analysis()
