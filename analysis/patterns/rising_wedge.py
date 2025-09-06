import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from .utils import find_trend_line

def check_rising_wedge(df: pd.DataFrame, config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Identifies Rising Wedge patterns.
    A Rising Wedge is a bearish pattern that begins wide at the bottom and contracts as prices move higher.
    It involves two converging trendlines, both angled upwards.
    """
    found_patterns = []

    if len(highs) < 2 or len(lows) < 2:
        return found_patterns

    search_data = df.tail(50)
    window_highs = [h for h in highs if h['index'] >= search_data.index[0]]
    window_lows = [l for l in lows if l['index'] >= search_data.index[0]]

    if len(window_highs) < 2 or len(window_lows) < 2:
        return found_patterns

    upper_trend = find_trend_line([p['index'] for p in window_highs], [p['price'] for p in window_highs])
    lower_trend = find_trend_line([p['index'] for p in window_lows], [p['price'] for p in window_lows])

    # 1. Both lines must be upward sloping
    if upper_trend['slope'] <= 0 or lower_trend['slope'] <= 0:
        return found_patterns

    # 2. The lines must be converging (lower line steeper than upper line)
    if lower_trend['slope'] <= upper_trend['slope']:
        return found_patterns

    # 3. Check if the current price is still within the wedge
    resistance_price_now = upper_trend['slope'] * df.index[-1] + upper_trend['intercept']
    support_price_now = lower_trend['slope'] * df.index[-1] + lower_trend['intercept']

    if current_price > resistance_price_now * (1 + price_tolerance):
        return found_patterns

    status = "قيد التكوين 🟡"
    if current_price < support_price_now:
        status = "مكتمل ✅"

    convergence_rate = abs(lower_trend['slope'] - upper_trend['slope'])
    confidence = 70 + (len(window_highs) + len(window_lows) - 4) * 5 + convergence_rate * 100

    wedge_height = max(p['price'] for p in window_highs) - min(p['price'] for p in window_lows)
    target = support_price_now - wedge_height

    pattern_info = {
        "name": "وتد صاعد (Rising Wedge)",
        "status": status,
        "confidence": min(95, int(confidence)),
        "resistance_line": resistance_price_now,
        "support_line": support_price_now,
        "calculated_target": target,
        "time_identified": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    found_patterns.append(pattern_info)

    return found_patterns
