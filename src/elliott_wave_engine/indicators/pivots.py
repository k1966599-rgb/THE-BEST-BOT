import pandas as pd
from scipy.signal import find_peaks
from typing import List, Dict, Any

def find_pivots(df: pd.DataFrame, prominence: float = 1.0) -> List[Dict[str, Any]]:
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
