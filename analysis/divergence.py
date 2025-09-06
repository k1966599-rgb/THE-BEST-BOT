import pandas as pd
from typing import List, Dict

from .patterns.utils import find_pivots

def _find_divergence_in_pivots(price_pivots: List[Dict], indicator_pivots: List[Dict], trend: str) -> List[Dict]:
    """
    A helper function to find divergence by comparing lists of price and indicator pivots.
    """
    divergences = []
    if not price_pivots or not indicator_pivots or len(price_pivots) < 2 or len(indicator_pivots) < 2:
        return divergences

    last_indicator_pivot = indicator_pivots[-1]
    last_price_pivot = min(price_pivots, key=lambda p: abs(p['index'] - last_indicator_pivot['index']))

    if abs(last_price_pivot['index'] - last_indicator_pivot['index']) > 5:
        return divergences

    for i in range(len(indicator_pivots) - 2, -1, -1):
        prev_indicator_pivot = indicator_pivots[i]
        prev_price_pivot = min(price_pivots, key=lambda p: abs(p['index'] - prev_indicator_pivot['index']))

        if abs(prev_price_pivot['index'] - prev_indicator_pivot['index']) > 5:
            continue

        is_divergence = False
        if trend == 'bullish':
            if last_price_pivot['value'] < prev_price_pivot['value'] and last_indicator_pivot['value'] > prev_indicator_pivot['value']:
                is_divergence = True
        elif trend == 'bearish':
            if last_price_pivot['value'] > prev_price_pivot['value'] and last_indicator_pivot['value'] < prev_indicator_pivot['value']:
                is_divergence = True

        if is_divergence:
            divergences.append({
                "type": "Bullish" if trend == 'bullish' else "Bearish",
                "price_pivots": (prev_price_pivot, last_price_pivot),
                "indicator_pivots": (prev_indicator_pivot, last_indicator_pivot)
            })
            break

    return divergences


def detect_divergence(price_series: pd.Series, indicator_series: pd.Series, distance: int = 5) -> List[Dict]:
    """
    Detects bullish and bearish divergences between a price series and an indicator series.
    """
    if price_series.empty or indicator_series.empty or len(price_series) != len(indicator_series):
        return []

    price_highs = find_pivots(price_series, prominence_multiplier=0.5, distance=distance)
    price_lows = find_pivots(-price_series, prominence_multiplier=0.5, distance=distance)
    indicator_highs = find_pivots(indicator_series, prominence_multiplier=0.3, distance=distance)
    indicator_lows = find_pivots(-indicator_series, prominence_multiplier=0.3, distance=distance)

    for low in price_lows: low['value'] = -low['value']
    for low in indicator_lows: low['value'] = -low['value']

    all_divergences = []

    bearish_divs = _find_divergence_in_pivots(price_highs, indicator_highs, 'bearish')
    all_divergences.extend(bearish_divs)

    bullish_divs = _find_divergence_in_pivots(price_lows, indicator_lows, 'bullish')
    all_divergences.extend(bullish_divs)

    return all_divergences
