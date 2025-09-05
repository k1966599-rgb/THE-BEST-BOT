import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from positive_indicators_generator import generate_positive_indicators

def test_rsi_indicator():
    """Test that the RSI oversold indicator is correctly generated."""
    mock_analysis = {
        'indicators': {'rsi': 25, 'macd_is_bullish': False},
        'support_resistance': {},
        'patterns': {},
        'fibonacci': {}
    }
    indicators = generate_positive_indicators(mock_analysis, current_price=100)
    assert "✅ RSI يقترب من منطقة تشبع البيع" in indicators

def test_macd_indicator():
    """Test that the MACD bullish indicator is correctly generated."""
    mock_analysis = {
        'indicators': {'rsi': 50, 'macd_is_bullish': True},
        'support_resistance': {},
        'patterns': {},
        'fibonacci': {}
    }
    indicators = generate_positive_indicators(mock_analysis, current_price=100)
    assert "✅ MACD يظهر إشارة إيجابية" in indicators

def test_no_indicators():
    """Test that no indicators are generated when conditions are not met."""
    mock_analysis = {
        'indicators': {'rsi': 50, 'macd_is_bullish': False},
        'support_resistance': {},
        'patterns': {},
        'fibonacci': {}
    }
    indicators = generate_positive_indicators(mock_analysis, current_price=100)
    assert len(indicators) == 0
