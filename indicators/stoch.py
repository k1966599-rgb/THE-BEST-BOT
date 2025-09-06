import pandas as pd
import pandas_ta as ta

def calculate_stoch(df: pd.DataFrame, k: int = 14, d: int = 3, smooth_k: int = 3):
    """
    Calculates the Stochastic Oscillator (STOCH).

    :param df: DataFrame with 'High', 'Low', 'Close' prices.
    :param k: The FastK period.
    :param d: The SlowD period.
    :param smooth_k: The SlowK period.
    """
    df.ta.stoch(k=k, d=d, smooth_k=smooth_k, append=True)
