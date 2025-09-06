import pandas as pd
import pandas_ta as ta

def calculate_obv(df: pd.DataFrame):
    """
    Calculates the On-Balance Volume (OBV).

    :param df: DataFrame with 'Close' and 'Volume' data.
    """
    df.ta.obv(append=True)
