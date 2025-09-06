import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from typing import Dict, List

def calculate_dynamic_confidence(df: pd.DataFrame, config: dict, base_confidence: int, is_bullish: bool) -> int:
    """
    Calculates a dynamic confidence score based on volume, trend strength (ADX), and momentum (RSI).
    """
    if len(df) == 0: return base_confidence

    confidence = base_confidence
    latest_data = df.iloc[-1]

    # Volume Confirmation
    try:
        breakout_volume = latest_data['Volume']
        avg_volume = df['Volume'].rolling(window=20).mean().iloc[-1]
        if breakout_volume > avg_volume * 1.5:
            confidence += 10
    except (KeyError, IndexError):
        pass

    # ADX Confirmation
    try:
        adx_key = f"ADX_{config.get('ADX_PERIOD', 14)}"
        if adx_key in df.columns:
            adx_value = latest_data[adx_key]
            if adx_value > 25:
                confidence += 10
    except (KeyError, IndexError):
        pass

    # RSI Confirmation
    try:
        rsi_key = f"RSI_{config.get('RSI_PERIOD', 14)}"
        if rsi_key in df.columns:
            rsi_value = latest_data[rsi_key]
            if is_bullish and rsi_value < 75:
                confidence += 5
            elif not is_bullish and rsi_value > 25:
                confidence += 5
    except (KeyError, IndexError):
        pass

    return min(confidence, 98)

def find_pivots(data_series: pd.Series, prominence_multiplier: float, distance: int) -> List[Dict]:
    """
    A generic function to find pivot points (highs or lows) in any given data series.
    To find lows, pass a negated series (-data_series).
    """
    if data_series.empty or len(data_series) < distance:
        return []

    # More robust prominence calculation
    series_std = data_series.std()
    series_range = data_series.max() - data_series.min()

    # Use a fraction of the range as a fallback for low-volatility data
    prominence_from_range = series_range * 0.1 # 10% of the range
    prominence_from_std = series_std * prominence_multiplier

    # Use the smaller of the two, but ensure it's not zero
    prominence = min(prominence_from_range, prominence_from_std) if prominence_from_range > 0 and prominence_from_std > 0 else \
                 max(prominence_from_range, prominence_from_std)

    if np.isnan(prominence) or prominence == 0:
        return []

    pivots_idx, _ = find_peaks(data_series, prominence=prominence, distance=distance)

    return [{'index': i, 'value': data_series.iloc[i]} for i in pivots_idx]

def get_price_pivots(data: pd.DataFrame, prominence_multiplier=0.8, distance=5) -> (List[Dict], List[Dict]):
    """
    Finds high and low pivot points specifically for price data (High and Low series).
    """
    if data.empty or 'High' not in data.columns or 'Low' not in data.columns:
        return [], []

    highs = find_pivots(data['High'], prominence_multiplier, distance)
    lows = find_pivots(-data['Low'], prominence_multiplier, distance)

    for low in lows:
        low['value'] = -low['value']

    for p in highs: p['price'] = p.pop('value')
    for p in lows: p['price'] = p.pop('value')

    return highs, lows

def get_pivots(data: pd.DataFrame, prominence_multiplier=0.8) -> (List[Dict], List[Dict]):
    return get_price_pivots(data, prominence_multiplier)
