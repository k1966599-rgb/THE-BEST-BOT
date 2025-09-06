import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from .utils import find_trend_line

def check_bull_flag(df: pd.DataFrame, config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Identifies Bull Flag patterns.
    A Bull Flag is a continuation pattern that occurs after a strong uptrend.
    It consists of a 'flagpole' (the initial sharp rise) and a 'flag' (a period of consolidation).
    """
    found_patterns = []

    # Need at least a few pivots to form a flag
    if len(highs) < 2 or len(lows) < 2:
        return found_patterns

    # Iterate through recent lows to find the base of a potential flagpole
    for i in range(len(lows) - 2, -1, -1):
        flagpole_start_low = lows[i]

        # Find the peak of the flagpole after this low
        potential_poles = [h for h in highs if h['time'] > flagpole_start_low['time']]
        if not potential_poles:
            continue

        flagpole_end_high = max(potential_poles, key=lambda x: x['price'])

        flagpole_height = flagpole_end_high['price'] - flagpole_start_low['price']

        # The flagpole must be a significant move
        if flagpole_height < df['Close'].mean() * 0.05: # At least 5% of average price
            continue

        # --- Now, find the flag part ---
        # The flag consists of lower highs and lower lows after the flagpole peak
        flag_highs = [h for h in highs if h['time'] > flagpole_end_high['time']]
        flag_lows = [l for l in lows if l['time'] > flagpole_end_high['time']]

        if len(flag_highs) < 2 or len(flag_lows) < 2:
            continue

        # The flag should not retrace more than 50% of the pole
        deepest_retracement = min(flag_lows, key=lambda x: x['price'])
        retracement_level = (flagpole_end_high['price'] - deepest_retracement['price']) / flagpole_height
        if retracement_level > 0.5:
            continue

        # Fit trendlines for the flag channel
        upper_trend = find_trend_line([p['time'] for p in flag_highs], [p['price'] for p in flag_highs])
        lower_trend = find_trend_line([p['time'] for p in flag_lows], [p['price'] for p in flag_lows])

        # Trendlines should be roughly parallel and downward sloping
        if upper_trend['slope'] >= 0 or lower_trend['slope'] >= 0:
            continue
        if abs(upper_trend['slope'] - lower_trend['slope']) > abs(upper_trend['slope'] * 0.5):
            continue

        # Check for breakout
        resistance_line_price_at_current_time = upper_trend['slope'] * len(df) + upper_trend['intercept']

        status = "قيد التكوين 🟡"
        if current_price > resistance_line_price_at_current_time:
            status = "مكتمل ✅"

        confidence = 75 # Base confidence for a bull flag
        if retracement_level < 0.382:
            confidence += 5 # Shallower retracement is better
        if len(flag_highs) > 2 and len(flag_lows) > 2:
            confidence += 5 # More touches on the channel lines

        pattern_info = {
            "name": "علم صاعد (Bull Flag)",
            "status": status,
            "confidence": min(95, confidence),
            "resistance_line": resistance_line_price_at_current_time,
            "support_line": lower_trend['slope'] * len(df) + lower_trend['intercept'],
            "calculated_target": current_price + flagpole_height,
            "time_identified": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        found_patterns.append(pattern_info)
        break # Found the most recent one, no need to check older ones

    return found_patterns
