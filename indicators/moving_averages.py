import pandas as pd
import pandas_ta as ta
from typing import List

def calculate_sma(df: pd.DataFrame, lengths: List[int]):
    """
    Calculates Simple Moving Averages (SMA) for specified lengths.

    :param df: DataFrame with 'Close' prices.
    :param lengths: A list of integers representing the lengths for the SMA.
    """
    for length in lengths:
        df.ta.sma(length=length, append=True)

def calculate_ema(df: pd.DataFrame, lengths: List[int]):
    """
    Calculates Exponential Moving Averages (EMA) for specified lengths.

    :param df: DataFrame with 'Close' prices.
    :param lengths: A list of integers representing the lengths for the EMA.
    """
    for length in lengths:
        df.ta.ema(length=length, append=True)
