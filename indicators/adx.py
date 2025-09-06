import pandas as pd
import pandas_ta as ta

def calculate_adx(df: pd.DataFrame, length: int = 14):
    """
    Calculates the Average Directional Index (ADX).

    :param df: DataFrame with 'High', 'Low', 'Close' prices.
    :param length: The time period.
    """
    df.ta.adx(length=length, append=True)
