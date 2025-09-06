import pandas as pd
import pandas_ta as ta

def calculate_bbands(df: pd.DataFrame, length: int = 20, std: float = 2.0):
    """
    Calculates Bollinger Bands (BBANDS).

    :param df: DataFrame with 'Close' prices.
    :param length: The time period for the moving average.
    :param std: The number of standard deviations.
    """
    df.ta.bbands(length=length, std=std, append=True)
