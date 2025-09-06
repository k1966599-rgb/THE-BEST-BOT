import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from .utils import find_trend_line

def check_bear_flag(df: pd.DataFrame, config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Identifies Bear Flag patterns.
    A Bear Flag is a continuation pattern that occurs after a strong downtrend.
    It consists of a 'flagpole' (the initial sharp drop) and a 'flag' (a period of consolidation).
    """
    found_patterns = []

    # Need at least a few pivots to form a flag
    if len(highs) < 2 or len(lows) < 2:
        return found_patterns

    # Iterate through recent highs to find the top of a potential flagpole
    for i in range(len(highs) - 2, -1, -1):
        flagpole_start_high = highs[i]

        # Find the bottom of the flagpole after this high
        potential_poles = [l for l in lows if l['time'] > flagpole_start_high['time']]
        if not potential_poles:
            continue

        flagpole_end_low = min(potential_poles, key=lambda x: x['price'])

        flagpole_height = flagpole_start_high['price'] - flagpole_end_low['price']

        # The flagpole must be a significant move
        if flagpole_height < df['Close'].mean() * 0.05: # At least 5% of average price
            continue

        # --- Now, find the flag part ---
        # The flag consists of higher highs and higher lows after the flagpole bottom
        flag_highs = [h for h in highs if h['time'] > flagpole_end_low['time']]
        flag_lows = [l for l in lows if l['time'] > flagpole_end_low['time']]

        if len(flag_highs) < 2 or len(flag_lows) < 2:
            continue

        # The flag should not retrace more than 50% of the pole
        highest_retracement = max(flag_highs, key=lambda x: x['price'])
        retracement_level = (highest_retracement['price'] - flagpole_end_low['price']) / flagpole_height
        if retracement_level > 0.5:
            continue

        # Fit trendlines for the flag channel
        upper_trend = find_trend_line([p['time'] for p in flag_highs], [p['price'] for p in flag_highs])
        lower_trend = find_trend_line([p['time'] for p in flag_lows], [p['price'] for p in flag_lows])

        # Trendlines should be roughly parallel and upward sloping
        if upper_trend['slope'] <= 0 or lower_trend['slope'] <= 0:
            continue
        if abs(upper_trend['slope'] - lower_trend['slope']) > abs(lower_trend['slope'] * 0.5):
            continue

        # Check for breakdown
        support_line_price_at_current_time = lower_trend['slope'] * len(df) + lower_trend['intercept']

        status = "قيد التكوين 🟡"
        if current_price < support_line_price_at_current_time:
            status = "مكتمل ✅"

        confidence = 75 # Base confidence for a bear flag
        if retracement_level < 0.382:
            confidence += 5
        if len(flag_highs) > 2 and len(flag_lows) > 2:
            confidence += 5

        pattern_info = {
            "name": "علم هابط (Bear Flag)",
            "status": status,
            "confidence": min(95, confidence),
            "resistance_line": upper_trend['slope'] * len(df) + upper_trend['intercept'],
            "support_line": support_line_price_at_current_time,
            "calculated_target": current_price - flagpole_height,
            "time_identified": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        found_patterns.append(pattern_info)
        break

    return found_patterns
