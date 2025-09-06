import pandas as pd
import pandas_ta as ta

def calculate_atr(df: pd.DataFrame, length: int = 14):
    """
    Calculates the Average True Range (ATR).

    :param df: DataFrame with 'High', 'Low', 'Close' prices.
    :param length: The time period.
    """
    df.ta.atr(length=length, append=True)
