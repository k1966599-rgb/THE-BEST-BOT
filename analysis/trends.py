import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, Any, Optional

def get_line_equation(p1: tuple, p2: tuple) -> Optional[Dict[str, float]]:
    """Calculates the slope and intercept of a line given two points."""
    x1, y1 = p1
    x2, y2 = p2
    if x2 == x1: return None
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return {'slope': slope, 'intercept': intercept}

class TrendAnalysis:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy() # Expects a dataframe with indicators already calculated
        if config is None: config = {}
        self.config = config
        self.short_period = config.get('TREND_SHORT_PERIOD', 20)
        self.medium_period = config.get('TREND_MEDIUM_PERIOD', 50)
        self.long_period = config.get('TREND_LONG_PERIOD', 100)

    def find_trend_lines(self) -> Dict[str, Optional[Dict]]:
        """Finds the most recent major uptrend and downtrend lines."""
        data = self.df.tail(self.long_period)
        if len(data) < 20: return {'uptrend': None, 'downtrend': None}
        prominence = data['Close'].std() * 0.75
        high_pivots_idx, _ = find_peaks(data['High'], prominence=prominence, distance=5)
        low_pivots_idx, _ = find_peaks(-data['Low'], prominence=prominence, distance=5)
        uptrend_line, downtrend_line = None, None
        if len(low_pivots_idx) >= 2:
            p1_idx, p2_idx = low_pivots_idx[-2], low_pivots_idx[-1]
            p1 = (p1_idx, data['Low'].iloc[p1_idx])
            p2 = (p2_idx, data['Low'].iloc[p2_idx])
            uptrend_line = get_line_equation(p1, p2)
        if len(high_pivots_idx) >= 2:
            p1_idx, p2_idx = high_pivots_idx[-2], high_pivots_idx[-1]
            p1 = (p1_idx, data['High'].iloc[p1_idx])
            p2 = (p2_idx, data['High'].iloc[p2_idx])
            downtrend_line = get_line_equation(p1, p2)
        return {'uptrend': uptrend_line, 'downtrend': downtrend_line}

    def get_comprehensive_trend_analysis(self) -> Dict[str, Any]:
        """
        Performs trend analysis using pre-calculated EMAs and ADX from the dataframe.
        """
        if len(self.df) < self.long_period:
            return {'error': f'Not enough data for Trend analysis.', 'total_score': 0, 'adx': 0}

        latest = self.df.iloc[-1]
        current_price = latest['Close']
        ema_short = latest[f'EMA_{self.short_period}']
        ema_medium = latest[f'EMA_{self.medium_period}']
        ema_long = latest[f'EMA_{self.long_period}']
        adx = latest[f'ADX_{self.config.get("ADX_PERIOD", 14)}']

        trend_direction_score = 0
        if current_price > ema_short > ema_medium: trend_direction_score = 2
        elif ema_short > ema_medium > ema_long: trend_direction_score = 3
        elif current_price < ema_short < ema_medium: trend_direction_score = -2
        elif ema_short < ema_medium < ema_long: trend_direction_score = -3

        trend_strength_score = trend_direction_score * 1.5 if adx > 25 else trend_direction_score * 0.5 if adx < 20 else trend_direction_score

        return {
            'trend_lines': self.find_trend_lines(),
            'strength_score': round(trend_strength_score, 2),
            'total_score': round(trend_strength_score, 2),
            'is_trending': bool(adx > 25),
            'adx': round(adx, 2)
        }
