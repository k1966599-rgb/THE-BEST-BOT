import pandas as pd
import pandas_ta as ta

def calculate_rsi(df: pd.DataFrame, length: int = 14):
    """
    Calculates the Relative Strength Index (RSI).

    :param df: DataFrame with 'Close' prices.
    :param length: The time period for the RSI calculation.
    """
    df.ta.rsi(length=length, append=True)
