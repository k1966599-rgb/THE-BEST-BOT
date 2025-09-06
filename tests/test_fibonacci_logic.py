import pytest
import sys
import os
import pandas as pd
import pandas_ta as ta
import json
import numpy as np

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis.fibonacci import FibonacciAnalysis

@pytest.fixture(scope="module")
def historical_data_df():
    """Loads sample historical data from a JSON file and returns a DataFrame."""
    # Using the test data file to ensure consistency
    file_path = os.path.join(os.path.dirname(__file__), '..', 'test_okx_data', 'BTC-USDT_historical.json')
    with open(file_path, 'r') as f:
        json_data = json.load(f)

    df = pd.DataFrame(json_data['data'])
    # Basic data cleaning and type conversion, similar to the main bot
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df.drop(columns=['date'], inplace=True) # Drop the non-numeric 'date' column
    df = df.astype(float)
    return df

@pytest.fixture(scope="module")
def df_with_indicators(historical_data_df):
    """
    Prepares the DataFrame with indicators, mimicking the process in main_bot.py.
    This is crucial for creating a realistic test environment for the analysis module.
    """
    df = historical_data_df.copy()
    # 1. Rename columns to be compatible with pandas_ta
    df.rename(columns={"high": "High", "low": "Low", "open": "Open", "close": "Close", "volume": "Volume"}, inplace=True)

    # 2. Define the same strategy as in main_bot.py
    MyStrategy = ta.Strategy(
        name="Comprehensive Strategy",
        description="Calculates all indicators needed for the bot",
        ta=[
            {"kind": "sma", "length": 20},
            {"kind": "sma", "length": 50},
            {"kind": "sma", "length": 200},
            {"kind": "ema", "length": 20},
            {"kind": "ema", "length": 50},
            {"kind": "ema", "length": 100},
            {"kind": "rsi"},
            {"kind": "macd"},
            {"kind": "bbands"},
            {"kind": "stoch"},
            {"kind": "atr"}, # This is the important one for the new logic
            {"kind": "obv"},
            {"kind": "adx"},
        ]
    )
    # 3. Run the strategy
    df.ta.strategy(MyStrategy)
    # In the real application, NaNs are handled by downstream modules, so we don't drop them here.
    return df

def test_fibonacci_analysis_runs_successfully(df_with_indicators):
    """
    Tests that the FibonacciAnalysis class can be instantiated and run its
    comprehensive analysis without raising errors, returning a valid structure.
    """
    # Ensure the fixture is providing data
    assert not df_with_indicators.empty, "Test fixture failed to provide a DataFrame with indicators."

    # Instantiate the analysis class with the prepared data
    fib_analysis = FibonacciAnalysis(df_with_indicators)

    # Run the analysis
    results = fib_analysis.get_comprehensive_fibonacci_analysis()

    # --- Assertions ---
    # 1. Check for no errors and correct basic structure
    assert results is not None
    assert isinstance(results, dict)
    assert 'error' not in results, f"Fibonacci analysis returned an error: {results.get('error')}"

    # 2. Check for mandatory keys
    expected_keys = ['retracement_levels', 'extension_levels', 'fib_score']
    for key in expected_keys:
        assert key in results, f"Result dictionary is missing the key: '{key}'"

    # 3. Check the types of the returned values
    assert isinstance(results['retracement_levels'], list)
    assert isinstance(results['extension_levels'], list)
    assert isinstance(results['fib_score'], (int, float))

    # 4. (Optional) Check content of levels if they exist
    if results['retracement_levels']:
        level_sample = results['retracement_levels'][0]
        assert 'level' in level_sample
        assert 'price' in level_sample
        assert isinstance(level_sample['price'], (float, np.floating))

    if results['extension_levels']:
        level_sample = results['extension_levels'][0]
        assert 'level' in level_sample
        assert 'price' in level_sample
        assert isinstance(level_sample['price'], (float, np.floating))

    print("\nFibonacci analysis test passed successfully.")
    print(f"Fib Score: {results['fib_score']}")
    print(f"Retracement Levels Found: {len(results['retracement_levels'])}")
    print(f"Extension Levels Found: {len(results['extension_levels'])}")
