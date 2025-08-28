import pandas as pd
from scipy.signal import find_peaks
from typing import List, Dict, Any

def find_pivots(df: pd.DataFrame, prominence: float = 1.0) -> List[Dict[str, Any]]:
    # Robustness Patch: If the index is not a DatetimeIndex, attempt to fix it.
    # This is a workaround for an upstream bug where the index is being reset.
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'timestamp' in df.columns:
            # If the timestamp column exists, use it to rebuild the index.
            df = df.set_index('timestamp')
            if not isinstance(df.index, pd.DatetimeIndex):
                 # If the column is not already datetime, convert it.
                 df.index = pd.to_datetime(df.index)
        else:
            # If we can't fix it, raise an error with more context.
            raise TypeError(f"DataFrame index is not a DatetimeIndex and 'timestamp' column not found.")

    if 'high' not in df.columns or 'low' not in df.columns:
        raise ValueError("Input DataFrame must contain 'high' and 'low' columns.")
    high_peaks_indices, _ = find_peaks(df['high'], prominence=prominence)
    low_peaks_indices, _ = find_peaks(-df['low'], prominence=prominence)
    pivots = []
    for i in high_peaks_indices:
        pivots.append({"time": df.index[i], "price": df['high'][i], "type": "H", "idx": i})
    for i in low_peaks_indices:
        pivots.append({"time": df.index[i], "price": df['low'][i], "type": "L", "idx": i})
    pivots.sort(key=lambda p: p['time'])
    if not pivots: return []
    cleaned_pivots = [pivots[0]]
    for i in range(1, len(pivots)):
        if pivots[i]['type'] != cleaned_pivots[-1]['type']:
            cleaned_pivots.append(pivots[i])
    return cleaned_pivots
