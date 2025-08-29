import pytest
import pandas as pd
from src.elliott_wave_engine.core.wave_structure import WavePoint, WavePattern
from src.trading.risk_management import calculate_fibonacci_trade_parameters

# Helper to create a mock WavePattern
def create_mock_pattern(points_data, pattern_type="ImpulseUp"):
    # Mocking the 'type' and 'idx' fields required by the WavePoint constructor.
    # These are not used by the function under test, but are required for instantiation.
    points = [WavePoint(price=p, time=t, type='pivot', idx=t) for t, p in enumerate(points_data)]
    pattern = WavePattern(
        pattern_type=pattern_type,
        points=points,
        confidence_score=85.0
    )
    return pattern

def test_proactive_wave_5_trade_setup():
    """
    Tests the new proactive logic for entering a trade to capture Wave 5.
    This test simulates a valid 4-wave impulse pattern.
    """
    # GIVEN a 5-point impulse pattern (P0, P1, P2, P3, P4), where W4 > W1
    # P0=100, P1=110, P2=105, P3=120, P4=115
    # Wave 1 height = 10
    # Wave 4 (115) is above Wave 1 (110), so the pattern is valid.
    mock_impulse_p0_p4 = create_mock_pattern([100, 110, 105, 120, 115])

    # WHEN we calculate the trade parameters for this pattern
    trade_setup = calculate_fibonacci_trade_parameters(mock_impulse_p0_p4, pd.DataFrame())

    # THEN we should get a valid trade setup
    assert trade_setup is not None
    assert trade_setup['reason'] == "توقع استكمال الموجة الدافعة (الموجة 5) (ImpulseUp)"
    assert trade_setup['pattern_type'] == "ImpulseUp"

    # AND the parameters should be calculated correctly
    # Entry should be at P4's price
    assert trade_setup['entry'] == 115
    # Stop loss should be at P1's price
    assert trade_setup['stop_loss'] == 110

    # AND the targets should be correct fib extensions of Wave 1 from P4
    # W1 height = 110 - 100 = 10
    # Target 1 (0.618) = 115 + 10 * 0.618 = 121.18
    # Target 2 (1.0)   = 115 + 10 * 1.0   = 125.0
    # Target 3 (1.618) = 115 + 10 * 1.618 = 131.18
    assert len(trade_setup['targets']) == 3
    assert pytest.approx(trade_setup['targets'][0]) == 121.18
    assert pytest.approx(trade_setup['targets'][1]) == 125.0
    assert pytest.approx(trade_setup['targets'][2]) == 131.18

def test_proactive_wave_5_trade_setup_invalid_pattern():
    """
    Tests that the proactive logic rejects a pattern where Wave 4 overlaps Wave 1.
    """
    # GIVEN a 5-point impulse pattern where P4 (108) <= P1 (110)
    mock_invalid_impulse = create_mock_pattern([100, 110, 105, 120, 108])

    # WHEN we calculate the trade parameters
    trade_setup = calculate_fibonacci_trade_parameters(mock_invalid_impulse, pd.DataFrame())

    # THEN the setup should be rejected
    assert trade_setup is None
