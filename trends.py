import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from typing import Dict, Any, Optional

def get_line_equation(p1: tuple, p2: tuple) -> Optional[Dict[str, float]]:
    """Calculates the slope and intercept of a line given two points."""
    x1, y1 = p1
    x2, y2 = p2
    if x2 == x1:
        return None  # Vertical line, undefined slope
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return {'slope': slope, 'intercept': intercept}

class TrendAnalysis:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.config = config
        self.short_period = config.get('TREND_SHORT_PERIOD', 20)
        self.medium_period = config.get('TREND_MEDIUM_PERIOD', 50)
        self.long_period = config.get('TREND_LONG_PERIOD', 100)

    def find_trend_lines(self) -> Dict[str, Optional[Dict]]:
        """Finds the most recent major uptrend and downtrend lines."""
        data = self.df.tail(self.long_period)
        if len(data) < 20:
            return {'uptrend': None, 'downtrend': None}

        # Find significant pivot points
        prominence = data['close'].std() * 0.75
        high_pivots_idx, _ = find_peaks(data['high'], prominence=prominence, distance=5)
        low_pivots_idx, _ = find_peaks(-data['low'], prominence=prominence, distance=5)

        uptrend_line = None
        downtrend_line = None

        # Find uptrend line from last two major lows
        if len(low_pivots_idx) >= 2:
            p1_idx, p2_idx = low_pivots_idx[-2], low_pivots_idx[-1]
            p1 = (p1_idx, data['low'].iloc[p1_idx])
            p2 = (p2_idx, data['low'].iloc[p2_idx])
            uptrend_line = get_line_equation(p1, p2)

        # Find downtrend line from last two major highs
        if len(high_pivots_idx) >= 2:
            p1_idx, p2_idx = high_pivots_idx[-2], high_pivots_idx[-1]
            p1 = (p1_idx, data['high'].iloc[p1_idx])
            p2 = (p2_idx, data['high'].iloc[p2_idx])
            downtrend_line = get_line_equation(p1, p2)

        return {'uptrend': uptrend_line, 'downtrend': downtrend_line}

    def get_comprehensive_trend_analysis(self) -> Dict[str, Any]:
        if len(self.df) < self.long_period:
            return {'error': f'Not enough data for Trend analysis.', 'total_score': 0}

        # --- Trend Strength using SMAs ---
        current_price = self.df['close'].iloc[-1]
        sma_short = self.df['close'].rolling(window=self.short_period).mean().iloc[-1]
        sma_medium = self.df['close'].rolling(window=self.medium_period).mean().iloc[-1]
        sma_long = self.df['close'].rolling(window=self.long_period).mean().iloc[-1]

        trend_strength_score = 0
        if current_price > sma_short > sma_medium: trend_strength_score += 2
        if sma_medium > sma_long: trend_strength_score += 1
        if current_price < sma_short < sma_medium: trend_strength_score -= 2
        if sma_medium < sma_long: trend_strength_score -= 1

        # --- Trend Lines ---
        trend_lines = self.find_trend_lines()

        # Add to score if price is respecting the trend line
        if trend_lines.get('uptrend'):
            slope = trend_lines['uptrend']['slope']
            intercept = trend_lines['uptrend']['intercept']
            trend_line_price_now = slope * (len(self.df) - 1) + intercept
            if current_price > trend_line_price_now:
                trend_strength_score += 1

        if trend_lines.get('downtrend'):
            slope = trend_lines['downtrend']['slope']
            intercept = trend_lines['downtrend']['intercept']
            trend_line_price_now = slope * (len(self.df) - 1) + intercept
            if current_price < trend_line_price_now:
                trend_strength_score -= 1

        return {
            'trend_lines': trend_lines,
            'strength_score': trend_strength_score,
            'total_score': trend_strength_score
        }
