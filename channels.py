import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any

class PriceChannels:
    """
    وحدة تحليل القنوات السعرية المتقدمة
    تحدد القناة السعرية الأكثر وضوحًا وتوفر بياناتها للتقرير.
    """
    def __init__(self, df: pd.DataFrame, lookback_period: int = 50):
        self.df = df.copy()
        self.lookback = lookback_period

    def detect_best_channel(self) -> Dict:
        """
        Detects the most significant channel (linear regression based) and returns its details.
        """
        data = self.df.tail(self.lookback)
        if len(data) < 10:
            return {'error': 'Not enough data for channel analysis.'}

        x = np.arange(len(data))
        highs = data['high'].values
        lows = data['low'].values

        try:
            slope_high, intercept_high, r_high, _, _ = stats.linregress(x, highs)
            slope_low, intercept_low, r_low, _, _ = stats.linregress(x, lows)
        except ValueError:
            return {'error': 'Could not calculate linear regression.'}

        # Determine channel type based on slopes
        if slope_high > 0 and slope_low > 0:
            channel_type = "قناة صاعدة"
        elif slope_high < 0 and slope_low < 0:
            channel_type = "قناة هابطة"
        elif slope_high < 0 and slope_low > 0:
            channel_type = "مثلث متماثل"
        else:
            channel_type = "قناة عرضية/متوسعة"

        # Calculate current channel boundaries
        current_upper = slope_high * (len(x) - 1) + intercept_high
        current_lower = slope_low * (len(x) - 1) + intercept_low

        # Scoring
        # A higher score for channels with high correlation (straighter lines)
        # and for trending channels vs. sideways.
        r_strength = (abs(r_high) + abs(r_low)) / 2
        slope_strength = 1 + abs(slope_high + slope_low) / (data['close'].mean() * 0.001)
        score = r_strength * slope_strength

        return {
            "type": channel_type,
            "upper_bound": round(current_upper, 4),
            "lower_bound": round(current_lower, 4),
            "strength_r": round(r_strength, 2),
            "score": round(score, 2)
        }

    def get_comprehensive_channel_analysis(self) -> Dict:
        """
        Returns a summary of the most prominent channel found.
        """
        best_channel = self.detect_best_channel()

        if 'error' in best_channel:
            return {
                'channel_info': "لا توجد قناة واضحة",
                'total_score': 0
            }

        # The final score is the calculated channel score
        total_score = best_channel.get('score', 0)

        # The main info string for the report
        channel_info = (
            f"{best_channel.get('type', 'N/A')}: "
            f"${best_channel.get('lower_bound', 0):,.2f} - ${best_channel.get('upper_bound', 0):,.2f}"
        )

        return {
            'channel_info': channel_info,
            'total_score': total_score,
            'details': best_channel
        }
