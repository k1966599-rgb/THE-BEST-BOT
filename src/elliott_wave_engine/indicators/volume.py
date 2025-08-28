import pandas as pd
from typing import Dict, Any
import pandas_ta as ta

def calculate_volume_sma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    if 'volume' not in df.columns: raise ValueError("Input DataFrame must contain a 'volume' column.")
    return df.ta.sma(df['volume'], length=length)

def analyze_wave_volume(df: pd.DataFrame, wave_points: Dict[str, Any]) -> Dict[str, Any]:
    if 'volume' not in df.columns:
        return {'pass': False, 'details': 'Volume data not available.'}
    try:
        points = list(wave_points.values())
        if len(points) < 6:
            return {'pass': False, 'details': 'Not enough points for impulse volume analysis.'}
        p0, p1, p2, p3, p4, p5 = points
        vol_w1 = df.loc[p0['time']:p1['time']]['volume'].sum()
        vol_w3 = df.loc[p2['time']:p3['time']]['volume'].sum()
        vol_w5 = df.loc[p4['time']:p5['time']]['volume'].sum()
        passed = vol_w3 > vol_w1 and vol_w3 > vol_w5
        details = f"Volume: W1({vol_w1:,.0f}), W3({vol_w3:,.0f}), W5({vol_w5:,.0f}). Guideline (W3 is highest): {'Pass' if passed else 'Fail'}"
        return {'pass': passed, 'details': details}
    except (KeyError, IndexError):
        return {'pass': False, 'details': 'Invalid wave points for volume analysis.'}
    except Exception as e:
        return {'pass': False, 'details': f'Volume analysis error: {e}'}
