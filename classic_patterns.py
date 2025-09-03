import pandas as pd
import numpy as np
from typing import Dict, List
from scipy.signal import find_peaks

class ClassicPatterns:
    """
    وحدة تحليل النماذج الكلاسيكية المتقدمة
    """
    def __init__(self, df: pd.DataFrame, lookback_period: int = 90):
        self.df = df.copy()
        self.lookback_period = lookback_period
        self.data = self.df.tail(lookback_period)
        self.current_price = self.data['close'].iloc[-1] if not self.data.empty else 0

    def get_comprehensive_pattern_analysis(self) -> Dict:
        if len(self.data) < self.lookback_period:
            return {'error': f'Not enough data. Need {self.lookback_period}, got {len(self.data)}.', 'pattern_score': 0, 'found_patterns': []}

        patterns = []

        # --- Double Top & Double Bottom ---
        highs_indices, _ = find_peaks(self.data['high'], prominence=self.data['high'].std()*0.8, distance=10)
        lows_indices, _ = find_peaks(-self.data['low'], prominence=self.data['low'].std()*0.8, distance=10)

        if len(highs_indices) >= 2:
            p1_idx, p2_idx = highs_indices[-2], highs_indices[-1]
            p1, p2 = self.data['high'].iloc[p1_idx], self.data['high'].iloc[p2_idx]
            if abs(p1 - p2) / p1 < 0.03:
                valley_idx = self.data['low'].iloc[p1_idx:p2_idx].idxmin()
                valley_price = self.data.loc[valley_idx]['low']
                status = "مكتمل ✅" if self.current_price < valley_price else "في التكوين 🟡"
                patterns.append({'name': 'Double Top', 'status': status, 'target': valley_price - (p1 - valley_price)})

        if len(lows_indices) >= 2:
            v1_idx, v2_idx = lows_indices[-2], lows_indices[-1]
            v1, v2 = self.data['low'].iloc[v1_idx], self.data['low'].iloc[v2_idx]
            if abs(v1 - v2) / v1 < 0.03:
                peak_idx = self.data['high'].iloc[v1_idx:v2_idx].idxmax()
                peak_price = self.data.loc[peak_idx]['high']
                status = "مكتمل ✅" if self.current_price > peak_price else "في التكوين 🟡"
                patterns.append({'name': 'Double Bottom', 'status': status, 'target': peak_price + (peak_price - v1)})

        # --- Triangles & Wedges (Simplified) ---
        volatility = self.data['high'] - self.data['low']
        if len(volatility) > 40:
            recent_volatility = volatility.tail(10).mean()
            past_volatility = volatility.head(30).mean()
            if recent_volatility < past_volatility * 0.5:
                 patterns.append({'name': 'Triangle/Wedge Forming', 'status': 'في التكوين 🟡', 'target': self.current_price * (1 + (past_volatility/self.current_price)*2) })

        # Calculate score
        pattern_score = 0
        for p in patterns:
            if p.get('status') == "مكتمل ✅":
                pattern_score += 2 if 'Bottom' in p['name'] else -2
            else:
                pattern_score += 1 if 'Bottom' in p['name'] else -1

        return {
            'found_patterns': patterns,
            'pattern_score': pattern_score
        }
