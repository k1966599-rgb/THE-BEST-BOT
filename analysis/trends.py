import pandas as pd
from typing import Dict, Any

class TrendAnalysis:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.config = config
        # Using more descriptive names for periods based on their default values
        self.short_period = config.get('TREND_SHORT_PERIOD', 20)
        self.medium_period = config.get('TREND_MEDIUM_PERIOD', 50)
        self.long_period = config.get('TREND_LONG_PERIOD', 100)
        self.adx_period = config.get('ADX_PERIOD', 14)

    def get_comprehensive_trends_analysis(self) -> Dict[str, Any]:
        """
        Performs trend analysis using pre-calculated EMAs and ADX from the dataframe.
        This focuses on trend direction and strength based on indicators.
        """
        required_len = self.long_period
        if len(self.df) < required_len:
            return {'error': f'Not enough data for Trend analysis. Need {required_len} periods.', 'total_score': 0}

        latest = self.df.iloc[-1]

        # Ensure required columns exist
        required_cols = [
            'Close',
            f'EMA_{self.short_period}',
            f'EMA_{self.medium_period}',
            f'EMA_{self.long_period}',
            f'ADX_{self.adx_period}'
        ]
        if not all(col in latest.index for col in required_cols):
            return {'error': 'One or more required indicator columns are missing for trend analysis.', 'total_score': 0}

        current_price = latest['Close']
        ema_short = latest[f'EMA_{self.short_period}']
        ema_medium = latest[f'EMA_{self.medium_period}']
        ema_long = latest[f'EMA_{self.long_period}']
        adx = latest[f'ADX_{self.adx_period}']

        trend_direction_score = 0
        # More robust conditions
        if current_price > ema_short and ema_short > ema_medium: trend_direction_score = 2
        elif ema_short > ema_medium and ema_medium > ema_long: trend_direction_score = 3
        elif current_price < ema_short and ema_short < ema_medium: trend_direction_score = -2
        elif ema_short < ema_medium and ema_medium < ema_long: trend_direction_score = -3

        # Calculate final score based on trend strength (ADX)
        if adx > 25:
            total_score = trend_direction_score * 1.5
        elif adx < 20:
            total_score = trend_direction_score * 0.5
        else:
            total_score = trend_direction_score

        return {
            'total_score': round(total_score, 2),
            'trend_direction': 'Uptrend' if trend_direction_score > 0 else 'Downtrend' if trend_direction_score < 0 else 'Sideways',
            'is_trending': bool(adx > 25),
            'adx_value': round(adx, 2)
        }
