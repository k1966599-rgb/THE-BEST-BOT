import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from .utils import find_trend_line

def check_falling_wedge(df: pd.DataFrame, config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Identifies Falling Wedge patterns.
    A Falling Wedge is a bullish pattern that begins wide at the top and contracts as prices move lower.
    It involves two converging trendlines, both angled downwards.
    """
    found_patterns = []

    # Need at least 2 highs and 2 lows to form the wedge
    if len(highs) < 2 or len(lows) < 2:
        return found_patterns

    # Consider the last 30-50 candles for wedge formation
    search_data = df.tail(50)

    # Filter pivots within this search window
    window_highs = [h for h in highs if h['index'] >= search_data.index[0]]
    window_lows = [l for l in lows if l['index'] >= search_data.index[0]]

    if len(window_highs) < 2 or len(window_lows) < 2:
        return found_patterns

    # Fit trendlines to the highs and lows
    upper_trend = find_trend_line([p['index'] for p in window_highs], [p['price'] for p in window_highs])
    lower_trend = find_trend_line([p['index'] for p in window_lows], [p['price'] for p in window_lows])

    # 1. Both lines must be downward sloping
    if upper_trend['slope'] >= 0 or lower_trend['slope'] >= 0:
        return found_patterns

    # 2. The lines must be converging (upper line steeper than lower line)
    if upper_trend['slope'] >= lower_trend['slope']:
        return found_patterns

    # 3. Check if the current price is still within the wedge
    resistance_price_now = upper_trend['slope'] * df.index[-1] + upper_trend['intercept']
    support_price_now = lower_trend['slope'] * df.index[-1] + lower_trend['intercept']

    # Ignore if the wedge is too wide or already broken down
    if current_price < support_price_now * (1 - price_tolerance):
        return found_patterns

    # Determine status
    status = "قيد التكوين 🟡"
    if current_price > resistance_price_now:
        status = "مكتمل ✅"

    # Calculate confidence
    # Higher confidence for steeper convergence and more pivot points
    convergence_rate = abs(upper_trend['slope'] - lower_trend['slope'])
    confidence = 70 + (len(window_highs) + len(window_lows) - 4) * 5 + convergence_rate * 100

    # Calculate target
    wedge_height = max(p['price'] for p in window_highs) - min(p['price'] for p in window_lows)
    target = resistance_price_now + wedge_height

    pattern_info = {
        "name": "وتد هابط (Falling Wedge)",
        "status": status,
        "confidence": min(95, int(confidence)),
        "resistance_line": resistance_price_now,
        "support_line": support_price_now,
        "calculated_target": target,
        "time_identified": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    found_patterns.append(pattern_info)

    return found_patterns
