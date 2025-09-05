import pytest
import sys
import os
import pandas as pd

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indicators import TechnicalIndicators

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    # Create a dataframe with enough data to avoid 'Not enough data' errors
    data = {
        'high': [i for i in range(200, 400)],
        'low': [i for i in range(199, 399)],
        'close': [i for i in range(200, 400)]
    }
    df = pd.DataFrame(data)
    return df

def test_indicators_calculation(sample_dataframe):
    """Test that the indicator calculation runs without errors and returns the correct structure."""
    indicator_analysis = TechnicalIndicators(sample_dataframe)
    results = indicator_analysis.get_comprehensive_analysis()

    assert 'error' not in results
    assert 'total_score' in results
    assert 'rsi' in results
    assert 'macd_is_bullish' in results
    assert 'bollinger_bands' in results
    assert 'stochastic' in results
    assert 'atr' in results

    assert isinstance(results['total_score'], (int, float))
    assert isinstance(results['rsi'], float)
    assert isinstance(results['macd_is_bullish'], bool)
    assert isinstance(results['bollinger_bands'], dict)
    assert isinstance(results['stochastic'], dict)
    assert isinstance(results['atr'], float)
