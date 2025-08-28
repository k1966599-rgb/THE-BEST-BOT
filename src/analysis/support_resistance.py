import pandas as pd
from typing import List, Dict

def find_supply_demand_zones(df: pd.DataFrame, lookback: int = 50, threshold_multiplier: float = 2.0) -> List[Dict]:
    """
    Identifies potential Supply and Demand zones based on sharp price moves.
    This is a simplified implementation looking for candles that precede strong moves.
    """
    if df.empty or len(df) < 2:
        return []

    zones = []
    # Calculate the average body size over the lookback period
    avg_body_size = (abs(df['close'] - df['open'])).rolling(window=lookback, min_periods=1).mean()

    for i in range(1, len(df)):
        # A strong move is a candle with a body larger than the average
        is_strong_move = abs(df['close'][i] - df['open'][i]) > (avg_body_size.iloc[i-1] * threshold_multiplier)

        if not is_strong_move:
            continue

        base_candle = df.iloc[i-1]

        # Potential Demand Zone (a down candle followed by a strong up move)
        if df['close'][i] > df['open'][i] and base_candle['close'] < base_candle['open']:
            zone = {
                'type': 'demand',
                'top': base_candle['open'],
                'bottom': base_candle['close']
            }
            zones.append(zone)

        # Potential Supply Zone (an up candle followed by a strong down move)
        elif df['close'][i] < df['open'][i] and base_candle['close'] > base_candle['open']:
            zone = {
                'type': 'supply',
                'top': base_candle['high'],
                'bottom': base_candle['low']
            }
            zones.append(zone)

    # A simple way to merge overlapping zones could be added here for refinement
    return zones
