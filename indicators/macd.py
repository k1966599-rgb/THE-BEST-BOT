import pandas as pd
import pandas_ta as ta

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Calculates the Moving Average Convergence Divergence (MACD).

    :param df: DataFrame with 'Close' prices.
    :param fast: The fast period length.
    :param slow: The slow period length.
    :param signal: The signal period length.
    """
    df.ta.macd(fast=fast, slow=slow, signal=signal, append=True)
