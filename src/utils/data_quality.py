import pandas as pd
import logging

def clean_market_data(df: pd.DataFrame, interval_str: str) -> pd.DataFrame:
    """
    Cleans and validates the market data DataFrame.
    """
    if df.empty:
        return df

    # Remove duplicates
    initial_rows = len(df)
    df.drop_duplicates(subset='timestamp', inplace=True, keep='first')
    if len(df) < initial_rows:
        logging.warning(f"Removed {initial_rows - len(df)} duplicate rows.")

    # Check for invalid data
    invalid_ohlc = df[df['high'] < df['low']]
    if not invalid_ohlc.empty:
        logging.warning(f"Found {len(invalid_ohlc)} rows with high < low. Dropping them.")
        df = df[df['high'] >= df['low']]

    # Check for time gaps
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['time_diff'] = df['timestamp'].diff()

    try:
        if interval_str == 'D':
            expected_interval = pd.Timedelta(days=1)
        else:
            expected_interval = pd.Timedelta(minutes=int(interval_str))

        tolerance = expected_interval * 0.05 # 5% tolerance
        gaps = df[df['time_diff'] > (expected_interval + tolerance)]
        if not gaps.empty:
            logging.warning(f"Found {len(gaps)} significant time gaps in the data.")

    except ValueError:
        logging.error(f"Could not determine interval from string for gap check: {interval_str}")
    finally:
        df = df.drop(columns=['time_diff'])

    return df
