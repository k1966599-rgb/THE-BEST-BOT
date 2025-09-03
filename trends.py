import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Any

class TrendAnalysis:
    def __init__(self, df: pd.DataFrame, short_period: int = 20, medium_period: int = 50, long_period: int = 100):
        self.df = df.copy()
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period

    def get_comprehensive_trend_analysis(self) -> Dict[str, Any]:
        if len(self.df) < self.long_period:
            return {'error': f'Not enough data for Trend analysis. Need {self.long_period}, got {len(self.df)}.', 'total_score': 0}

        # --- Trend Strength ---
        current_price = self.df['close'].iloc[-1]
        sma_short = self.df['close'].rolling(window=self.short_period).mean().iloc[-1]
        sma_medium = self.df['close'].rolling(window=self.medium_period).mean().iloc[-1]
        sma_long = self.df['close'].rolling(window=self.long_period).mean().iloc[-1]

        trend_strength_score = 0
        if current_price > sma_short: trend_strength_score += 1
        else: trend_strength_score -= 1
        if sma_short > sma_medium: trend_strength_score += 1
        else: trend_strength_score -= 1
        if sma_medium > sma_long: trend_strength_score += 1
        else: trend_strength_score -= 1

        # --- Trend Angle ---
        recent_prices = self.df['close'].tail(self.short_period)
        x = np.arange(len(recent_prices))
        try:
            slope, _, r_value, _, _ = stats.linregress(x, recent_prices)
            angle = np.degrees(np.arctan(slope))
        except ValueError:
            slope, angle, r_value = 0, 0, 0

        # --- Trend Line (Simplified) ---
        # A full implementation is complex; we use the angle as a proxy
        trend_line_info = f"Trend Angle: {angle:.2f}° (R-value: {r_value:.2f})"

        return {
            'trend_line_info': trend_line_info,
            'strength_score': trend_strength_score,
            'total_score': trend_strength_score,
            'angle': angle
        }
