import pandas as pd
import pandas_ta as ta

def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    if 'close' not in df.columns: raise ValueError("Input DataFrame must contain a 'close' column.")
    # Use append=False to ensure only the RSI series is returned.
    return df.ta.rsi(length=length, append=False)

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    if 'close' not in df.columns: raise ValueError("Input DataFrame must contain a 'close' column.")
    # Use append=False to ensure only the MACD columns are returned, preventing join errors.
    return df.ta.macd(fast=fast, slow=slow, signal=signal, append=False)

def calculate_stoch_rsi(df: pd.DataFrame, length: int = 14, rsi_length: int = 14, k: int = 3, d: int = 3) -> pd.DataFrame:
    if 'close' not in df.columns: raise ValueError("Input DataFrame must contain a 'close' column.")
    # Use append=False to ensure only the StochRSI columns are returned
    return df.ta.stochrsi(length=length, rsi_length=rsi_length, k=k, d=d, append=False)
