"""
This package contains individual modules for calculating various technical indicators.
"""
import pandas as pd

from .moving_averages import calculate_sma, calculate_ema
from .rsi import calculate_rsi
from .macd import calculate_macd
from .bbands import calculate_bbands
from .stoch import calculate_stoch
from .atr import calculate_atr
from .obv import calculate_obv
from .adx import calculate_adx

def apply_all_indicators(df: pd.DataFrame):
    """
    Applies all technical indicators to the given DataFrame.
    This function calls the individual calculation function for each indicator.

    :param df: The DataFrame with financial data (must include High, Low, Open, Close, Volume).
    """
    # Note: The functions modify the DataFrame in-place.

    # Moving Averages
    calculate_sma(df, lengths=[20, 50, 200])
    calculate_ema(df, lengths=[20, 50, 100])

    # Oscillators and other indicators
    calculate_rsi(df)
    calculate_macd(df)
    calculate_bbands(df)
    calculate_stoch(df)
    calculate_atr(df)
    calculate_obv(df)
    calculate_adx(df)

    return df
