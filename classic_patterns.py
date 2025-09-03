import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from scipy import signal, stats
import warnings

warnings.filterwarnings('ignore')

class ClassicPatterns:
    """وحدة النماذج الكلاسيكية الشاملة"""

    def __init__(self, df: pd.DataFrame, lookback_period: int = 60, min_pattern_bars: int = 10):
        self.df = df.copy()
        self.lookback_period = lookback_period
        self.min_pattern_bars = min_pattern_bars
        self.patterns_found = []

    def detect_head_and_shoulders(self) -> List[Dict]:
        """كشف نموذج الرأس والكتفين (العادي والمعكوس)"""
        data = self.df.tail(self.lookback_period)
        if len(data) < self.min_pattern_bars: return []

        # إيجاد القمم والقيعان
        highs_indices = signal.find_peaks(data['high'], prominence=data['high'].std() / 2)[0]
        lows_indices = signal.find_peaks(-data['low'], prominence=data['low'].std() / 2)[0]

        patterns = []

        # البحث عن الرأس والكتفين
        for i in range(1, len(highs_indices) - 1):
            left_s, head, right_s = highs_indices[i-1], highs_indices[i], highs_indices[i+1]
            # التحقق من أن الرأس هو الأعلى
            if data['high'][head] > data['high'][left_s] and data['high'][head] > data['high'][right_s]:
                # البحث عن القيعان بين القمم (خط العنق)
                neckline_lows = [l for l in lows_indices if left_s < l < right_s]
                if len(neckline_lows) >= 2:
                    neckline_points = data['low'][neckline_lows]
                    neckline_price = neckline_points.mean() # تبسيط لخط العنق

                    price_target = neckline_price - (data['high'][head] - neckline_price)
                    patterns.append({'type': 'Head and Shoulders', 'direction': 'bearish', 'target': price_target, 'strength': 2})

        # البحث عن الرأس والكتفين المعكوس
        for i in range(1, len(lows_indices) - 1):
            left_s, head, right_s = lows_indices[i-1], lows_indices[i], lows_indices[i+1]
            if data['low'][head] < data['low'][left_s] and data['low'][head] < data['low'][right_s]:
                neckline_highs = [h for h in highs_indices if left_s < h < right_s]
                if len(neckline_highs) >= 2:
                    neckline_points = data['high'][neckline_highs]
                    neckline_price = neckline_points.mean()

                    price_target = neckline_price + (neckline_price - data['low'][head])
                    patterns.append({'type': 'Inverse H&S', 'direction': 'bullish', 'target': price_target, 'strength': 2})

        return patterns

    def detect_double_patterns(self) -> List[Dict]:
        """كشف نماذج القمة المزدوجة والقاع المزدوج"""
        data = self.df.tail(self.lookback_period)
        if len(data) < self.min_pattern_bars: return []

        highs_indices = signal.find_peaks(data['high'], prominence=data['high'].std()/3, distance=5)[0]
        lows_indices = signal.find_peaks(-data['low'], prominence=data['low'].std()/3, distance=5)[0]
        patterns = []

        # القمة المزدوجة
        for i in range(len(highs_indices) - 1):
            p1_idx, p2_idx = highs_indices[i], highs_indices[i+1]
            p1, p2 = data['high'][p1_idx], data['high'][p2_idx]

            # التحقق من تشابه القمم
            if abs(p1 - p2) / p1 < 0.03:
                valley = data['low'][p1_idx:p2_idx].min()
                if (p1 - valley) / p1 > 0.05: # عمق كافي
                    patterns.append({'type': 'Double Top', 'direction': 'bearish', 'target': valley - (p1 - valley), 'strength': 1.5})

        # القاع المزدوج
        for i in range(len(lows_indices) - 1):
            v1_idx, v2_idx = lows_indices[i], lows_indices[i+1]
            v1, v2 = data['low'][v1_idx], data['low'][v2_idx]
            if abs(v1 - v2) / v1 < 0.03:
                peak = data['high'][v1_idx:v2_idx].max()
                if (peak - v1) / v1 > 0.05:
                    patterns.append({'type': 'Double Bottom', 'direction': 'bullish', 'target': peak + (peak - v1), 'strength': 1.5})

        return patterns

    def get_comprehensive_pattern_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل للنماذج الكلاسيكية"""
        hs_patterns = self.detect_head_and_shoulders()
        double_patterns = self.detect_double_patterns()

        all_patterns = hs_patterns + double_patterns

        pattern_score = 0
        if all_patterns:
            for p in all_patterns:
                if p['direction'] == 'bullish':
                    pattern_score += p['strength']
                else:
                    pattern_score -= p['strength']

        if pattern_score >= 2: recommendation = "إشارات صعود قوية من النماذج"
        elif pattern_score > 0: recommendation = "إشارات صعود من النماذج"
        elif pattern_score <= -2: recommendation = "إشارات هبوط قوية من النماذج"
        elif pattern_score < 0: recommendation = "إشارات هبوط من النماذج"
        else: recommendation = "لا توجد إشارات نماذج واضحة"

        return {
            'all_patterns': all_patterns,
            'pattern_score': pattern_score,
            'recommendation': recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
