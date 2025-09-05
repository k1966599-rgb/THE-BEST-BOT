import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, List, Any

class ClassicPatterns:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy() # Expects a dataframe with indicators already calculated
        if config is None: config = {}
        self.lookback_period = config.get('PATTERN_LOOKBACK', 90)
        self.data = self.df.tail(self.lookback_period)
        self.current_price = self.data['Close'].iloc[-1] if not self.data.empty else 0
        self.price_tolerance = config.get('PATTERN_PRICE_TOLERANCE', 0.03)

    def _calculate_dynamic_confidence(self, base_confidence: int, breakout_candle_idx: int) -> int:
        """
        Calculates a dynamic confidence score based on volume and trend strength (ADX).
        """
        if breakout_candle_idx >= len(self.df) or breakout_candle_idx < 0:
            return base_confidence

        confidence = base_confidence

        # 1. Volume Confirmation
        breakout_volume = self.df['Volume'].iloc[breakout_candle_idx]
        avg_volume = self.df['Volume'].rolling(window=20).mean().iloc[breakout_candle_idx]
        if breakout_volume > avg_volume * 1.5:
            confidence += 10 # Strong volume confirmation

        # 2. ADX Confirmation (Trend Strength)
        adx_period = self.config.get('ADX_PERIOD', 14)
        adx_value = self.df[f'ADX_{adx_period}'].iloc[breakout_candle_idx]
        if adx_value > 25:
            confidence += 10 # Breakout occurred during a strong trend

        return min(confidence, 98) # Cap confidence at 98%

    def get_pivots(self, prominence_multiplier=0.8):
        if self.data.empty: return [], []
        prominence = self.data['Close'].std() * prominence_multiplier
        if np.isnan(prominence) or prominence == 0: return [], []
        high_pivots_idx, _ = find_peaks(self.data['High'], prominence=prominence, distance=5)
        low_pivots_idx, _ = find_peaks(-self.data['Low'], prominence=prominence, distance=5)
        highs = [{'index': i, 'price': self.data['High'].iloc[i]} for i in high_pivots_idx]
        lows = [{'index': i, 'price': self.data['Low'].iloc[i]} for i in low_pivots_idx]
        return highs, lows

    def check_ascending_triangle(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        patterns = []
        if len(highs) < 2 or len(lows) < 2: return patterns
        last_high = highs[-1]['price']
        resistance_highs = [h for h in highs if abs(h['price'] - last_high) / last_high < self.price_tolerance]
        if len(resistance_highs) < 2: return patterns
        resistance_line = np.mean([h['price'] for h in resistance_highs])
        trend_lows = [l for i, l in enumerate(lows) if i < len(lows) - 1 and lows[i+1]['price'] > l['price']]
        if not trend_lows: return patterns
        if trend_lows[-1]['price'] > resistance_line: return patterns
        height = resistance_line - trend_lows[0]['price']

        confidence = self._calculate_dynamic_confidence(70, highs[-1]['index'])

        patterns.append({
            'name': 'مثلث صاعد (Ascending Triangle)', 'status': 'قيد التكوين 🟡' if self.current_price < resistance_line else 'مكتمل ✅',
            'resistance_line': resistance_line, 'support_line_start': trend_lows[0]['price'],
            'calculated_target': resistance_line + height, 'confidence': confidence
        })
        return patterns

    def check_double_bottom(self, highs: List[Dict], lows: List[Dict]) -> List[Dict]:
        patterns = []
        if len(lows) < 2: return patterns
        l1, l2 = lows[-2], lows[-1]
        if abs(l1['price'] - l2['price']) / l1['price'] < self.price_tolerance:
            intervening_highs = [h for h in highs if h['index'] > l1['index'] and h['index'] < l2['index']]
            if intervening_highs:
                neckline_high = max(intervening_highs, key=lambda x: x['price'])
                neckline_price = neckline_high['price']
                height = neckline_price - (l1['price'] + l2['price']) / 2
                confidence = self._calculate_dynamic_confidence(65, neckline_high['index'])
                patterns.append({
                    'name': 'قاع مزدوج (Double Bottom)', 'status': 'مكتمل ✅' if self.current_price > neckline_price else 'قيد التكوين 🟡',
                    'neckline': neckline_price, 'bottom_1_price': l1['price'], 'bottom_2_price': l2['price'],
                    'calculated_target': neckline_price + height, 'confidence': confidence
                })
        return patterns

    # ... Other pattern checks (double top, H&S, etc.) would be refactored similarly ...
    def get_comprehensive_patterns_analysis(self) -> Dict:
        if len(self.data) < 20: return {'error': 'Not enough data.', 'pattern_score': 0, 'found_patterns': []}
        highs, lows = self.get_pivots()
        if not highs or not lows: return {'error': 'Could not determine pivots.', 'pattern_score': 0, 'found_patterns': []}

        all_patterns = []
        all_patterns.extend(self.check_ascending_triangle(highs, lows))
        all_patterns.extend(self.check_double_bottom(highs, lows))
        # Extend with other checks here

        pattern_score = 0
        for p in all_patterns:
            score_multiplier = 1 if 'قاع' in p['name'] or 'صاعد' in p['name'] else -1
            if p.get('status') == "مكتمل ✅": pattern_score += 2 * score_multiplier
            else: pattern_score += 1 * score_multiplier

        all_patterns.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return {'found_patterns': all_patterns, 'pattern_score': pattern_score, 'error': None}

    def get_comprehensive_pattern_analysis(self) -> Dict: # Keep for compatibility
        return self.get_comprehensive_patterns_analysis()
