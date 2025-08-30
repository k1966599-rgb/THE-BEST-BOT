import numpy as np
from typing import List, Dict, Any

def zigzag_pivots(highs: np.ndarray, lows: np.ndarray, threshold: float = 0.015) -> List[Dict[str, Any]]:
    """
    Identifies pivot points in a time series using the ZigZag algorithm on high/low prices.
    """
    if len(highs) == 0 or len(lows) == 0:
        return []

    pivots = []
    trend = 0  # 1 for up, -1 for down
    last_pivot_price = (highs[0] + lows[0]) / 2
    last_pivot_idx = 0

    # Start with the first point as a potential pivot
    last_pivot_val = highs[0]

    for i in range(1, len(highs)):
        if trend == 1: # Uptrend, looking for a high
            if highs[i] > last_pivot_val:
                last_pivot_val = highs[i]
                last_pivot_idx = i
            elif lows[i] < last_pivot_val * (1 - threshold):
                pivots.append({'idx': last_pivot_idx, 'price': last_pivot_val, 'type': 'H'})
                trend = -1
                last_pivot_val = lows[i]
                last_pivot_idx = i
        elif trend == -1: # Downtrend, looking for a low
            if lows[i] < last_pivot_val:
                last_pivot_val = lows[i]
                last_pivot_idx = i
            elif highs[i] > last_pivot_val * (1 + threshold):
                pivots.append({'idx': last_pivot_idx, 'price': last_pivot_val, 'type': 'L'})
                trend = 1
                last_pivot_val = highs[i]
                last_pivot_idx = i
        else: # Trend is not determined yet
            if highs[i] > last_pivot_val * (1 + threshold):
                trend = 1
                last_pivot_val = highs[i]
                last_pivot_idx = i
            elif lows[i] < last_pivot_val * (1 - threshold):
                trend = -1
                last_pivot_val = lows[i]
                last_pivot_idx = i

    # Add the last indeterminate pivot
    if pivots: # ensure there is at least one confirmed pivot
        last_confirmed_pivot = pivots[-1]
        if trend == 1 and last_pivot_price > last_confirmed_pivot['price']:
             pivots.append({'idx': last_pivot_idx, 'price': last_pivot_val, 'type': 'H'})
        elif trend == -1 and last_pivot_price < last_confirmed_pivot['price']:
            pivots.append({'idx': last_pivot_idx, 'price': last_pivot_val, 'type': 'L'})

    return pivots
