import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any

class PriceChannels:
    """
    وحدة تحليل القنوات السعرية المتقدمة
    """
    def __init__(self, df: pd.DataFrame, lookback_period: int = 50):
        self.df = df.copy()
        self.lookback = lookback_period

    def get_comprehensive_channel_analysis(self) -> Dict:
        """
        Returns a summary of the most prominent channel found.
        """
        if len(self.df) < self.lookback:
            return {'error': f'Not enough data for Channel analysis. Need {self.lookback}, got {len(self.df)}.', 'total_score': 0}

        data = self.df.tail(self.lookback)
        x = np.arange(len(data))
        highs = data['high'].values
        lows = data['low'].values

        try:
            slope_high, intercept_high, r_high, _, _ = stats.linregress(x, highs)
            slope_low, intercept_low, r_low, _, _ = stats.linregress(x, lows)
        except ValueError:
            return {'error': 'Could not calculate linear regression.', 'total_score': 0}

        if slope_high > 0 and slope_low > 0: channel_type = "قناة صاعدة"
        elif slope_high < 0 and slope_low < 0: channel_type = "قناة هابطة"
        elif slope_high < 0 and slope_low > 0: channel_type = "مثلث متماثل"
        else: channel_type = "قناة عرضية/متوسعة"

        current_upper = slope_high * (len(x) - 1) + intercept_high
        current_lower = slope_low * (len(x) - 1) + intercept_low

        r_strength = (abs(r_high) + abs(r_low)) / 2
        score = r_strength * 5 # Simple score based on correlation

        return {
            'channel_info': f"{channel_type}: ${current_lower:,.2f} - ${current_upper:,.2f}",
            'total_score': round(score, 2),
            'details': { "type": channel_type, "upper_bound": current_upper, "lower_bound": current_lower }
        }
