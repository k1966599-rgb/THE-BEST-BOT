import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any
import warnings

warnings.filterwarnings('ignore')

class PriceChannels:
    """وحدة القنوات السعرية"""

    def __init__(self, df: pd.DataFrame, lookback_period: int = 50):
        self.df = df.copy()
        self.lookback = lookback_period
        self.channels = {}

    def detect_linear_channel(self, method: str = 'linear_regression') -> Dict[str, Any]:
        """كشف القناة الخطية"""
        recent_data = self.df.tail(self.lookback).copy()
        x = np.arange(len(recent_data))

        highs = recent_data['high'].values
        lows = recent_data['low'].values
        closes = recent_data['close'].values

        if len(recent_data) < 2:
            return {'type': 'Linear Channel', 'error': 'Not enough data'}

        slope_close, intercept_close, r_value_close, _, _ = stats.linregress(x, closes)
        slope_high, intercept_high, r_value_high, _, _ = stats.linregress(x, highs)
        slope_low, intercept_low, r_value_low, _, _ = stats.linregress(x, lows)

        channel_width = np.mean(highs) - np.mean(lows)
        current_position = closes[-1]

        next_high = slope_high * len(x) + intercept_high
        next_low = slope_low * len(x) + intercept_low
        next_close = slope_close * len(x) + intercept_close

        channel_strength = min(abs(r_value_close), abs(r_value_high), abs(r_value_low))

        if channel_strength > 0.8: strength_desc = "قناة قوية جداً"
        elif channel_strength > 0.6: strength_desc = "قناة قوية"
        elif channel_strength > 0.4: strength_desc = "قناة متوسطة"
        else: strength_desc = "قناة ضعيفة"

        if slope_close > 0.001: direction, direction_score = "صاعدة", 2
        elif slope_close < -0.001: direction, direction_score = "هابطة", -2
        else: direction, direction_score = "عرضية", 0

        channel_range = next_high - next_low
        if channel_range > 0:
            position_ratio = (current_position - next_low) / channel_range
            if position_ratio > 0.8: position_desc, position_score = "قرب المقاومة العليا", -1
            elif position_ratio < 0.2: position_desc, position_score = "قرب الدعم السفلي", 1
            else: position_desc, position_score = "وسط القناة", 0
        else:
            position_desc, position_score, position_ratio = "قناة ضيقة", 0, 0.5

        return {
            'type': 'Linear Channel', 'direction': direction, 'direction_score': direction_score,
            'strength': channel_strength, 'strength_desc': strength_desc, 'upper_line': next_high,
            'lower_line': next_low, 'trend_line': next_close, 'channel_width': channel_width,
            'position_in_channel': position_ratio, 'position_desc': position_desc,
            'position_score': position_score, 'slope': slope_close
        }

    def detect_parallel_channel(self) -> Dict[str, Any]:
        """كشف القناة المتوازية"""
        recent_data = self.df.tail(self.lookback).copy()

        highs_idx, lows_idx = [], []
        for i in range(2, len(recent_data) - 2):
            if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-1] and
                recent_data['high'].iloc[i] > recent_data['high'].iloc[i+1]):
                highs_idx.append(i)
            if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-1] and
                recent_data['low'].iloc[i] < recent_data['low'].iloc[i+1]):
                lows_idx.append(i)

        if len(highs_idx) >= 2 and len(lows_idx) >= 2:
            last_highs = sorted(highs_idx)[-2:]
            last_lows = sorted(lows_idx)[-2:]

            high_slope = (recent_data['high'].iloc[last_highs[1]] - recent_data['high'].iloc[last_highs[0]]) / (last_highs[1] - last_highs[0])
            low_slope = (recent_data['low'].iloc[last_lows[1]] - recent_data['low'].iloc[last_lows[0]]) / (last_lows[1] - last_lows[0])

            slope_diff = abs(high_slope - low_slope)

            if slope_diff < 0.001 * np.mean(recent_data['close']): parallel_quality, parallel_score = "متوازية ممتازة", 3
            elif slope_diff < 0.005 * np.mean(recent_data['close']): parallel_quality, parallel_score = "متوازية جيدة", 2
            elif slope_diff < 0.01 * np.mean(recent_data['close']): parallel_quality, parallel_score = "متوازية متوسطة", 1
            else: parallel_quality, parallel_score = "غير متوازية", 0

            upper_projection = recent_data['high'].iloc[last_highs[-1]] + high_slope * (len(recent_data) - last_highs[-1])
            lower_projection = recent_data['low'].iloc[last_lows[-1]] + low_slope * (len(recent_data) - last_lows[-1])

            return {
                'type': 'Parallel Channel', 'upper_line': upper_projection, 'lower_line': lower_projection,
                'parallel_quality': parallel_quality, 'parallel_score': parallel_score
            }
        else:
            return {'type': 'Parallel Channel', 'error': 'Not enough swing points'}

    def detect_wedge_patterns(self) -> Dict[str, Any]:
        """كشف أنماط الإسفين"""
        recent_data = self.df.tail(self.lookback).copy()
        x = np.arange(len(recent_data))

        if len(recent_data) < 2:
            return {'type': 'Wedge Pattern', 'error': 'Not enough data'}

        highs = recent_data['high'].values
        slope_high, intercept_high, r_high, _, _ = stats.linregress(x, highs)
        lows = recent_data['low'].values
        slope_low, intercept_low, r_low, _, _ = stats.linregress(x, lows)

        wedge_type, wedge_signal, wedge_score = "", "", 0
        if slope_high < 0 and slope_low > 0:
            wedge_type, wedge_signal, wedge_score = "Symmetrical Triangle", "انتظار الكسر", 0
        elif slope_high < 0 and slope_low < 0:
            if abs(slope_high) < abs(slope_low):
                wedge_type, wedge_signal, wedge_score = "Falling Wedge", "إشارة صعود محتملة", 2
        elif slope_high > 0 and slope_low > 0:
            if slope_high > slope_low:
                wedge_type, wedge_signal, wedge_score = "Rising Wedge", "إشارة هبوط محتملة", -2

        return {
            'type': wedge_type, 'signal': wedge_signal, 'score': wedge_score,
            'upper_slope': slope_high, 'lower_slope': slope_low
        }

    def get_comprehensive_channel_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل للقنوات السعرية"""
        linear_channel = self.detect_linear_channel()
        parallel_channel = self.detect_parallel_channel()
        wedge_analysis = self.detect_wedge_patterns()

        total_score = (
            linear_channel.get('direction_score', 0) +
            linear_channel.get('position_score', 0) +
            parallel_channel.get('parallel_score', 0) +
            wedge_analysis.get('score', 0)
        )

        if total_score >= 4: main_recommendation = "إشارة شراء قوية من القنوات"
        elif total_score >= 2: main_recommendation = "إشارة شراء من القنوات"
        elif total_score >= -1: main_recommendation = "محايد - انتظار كسر القناة"
        else: main_recommendation = "إشارة بيع من القنوات"

        return {
            'linear_channel': linear_channel, 'parallel_channel': parallel_channel,
            'wedge_analysis': wedge_analysis, 'total_score': total_score,
            'recommendation': main_recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
