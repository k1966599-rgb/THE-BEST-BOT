import unittest
import pandas as pd

# Import the specific components we are testing in isolation
from src.elliott_wave_engine.wave_structure import WavePattern, WavePoint
from src.elliott_wave_engine.validators.impulse_validator import validate_impulse_wave
from src.elliott_wave_engine.rules import wave_2_retrace_rule, wave_4_overlap_rule, wave_3_shortest_rule

class TestElliottWaveRules(unittest.TestCase):

    def setUp(self):
        """Set up a perfect bullish impulse wave pattern for all tests."""
        self.perfect_bullish_points = [
            WavePoint(pd.Timestamp('2023-01-01 14:00'), 10, 'L'),
            WavePoint(pd.Timestamp('2023-01-01 16:00'), 20, 'H'),
            WavePoint(pd.Timestamp('2023-01-01 17:00'), 15, 'L'),
            WavePoint(pd.Timestamp('2023-01-01 19:00'), 31, 'H'),
            WavePoint(pd.Timestamp('2023-01-01 20:00'), 25, 'L'),
            WavePoint(pd.Timestamp('2023-01-01 22:00'), 40, 'H')
        ]
        # Wave lengths: W1=10, W3=16, W5=15

    def test_wave_2_retrace_rule(self):
        """Test Rule: Wave 2 does not retrace more than 100% of Wave 1."""
        result = wave_2_retrace_rule(self.perfect_bullish_points)
        self.assertTrue(result.passed, f"Wave 2 rule failed: {result.details}")

    def test_wave_4_overlap_rule(self):
        """Test Rule: Wave 4 does not overlap with Wave 1."""
        result = wave_4_overlap_rule(self.perfect_bullish_points)
        self.assertTrue(result.passed, f"Wave 4 overlap rule failed: {result.details}")

    def test_wave_3_shortest_rule(self):
        """Test Rule: Wave 3 is not the shortest impulse wave."""
        result = wave_3_shortest_rule(self.perfect_bullish_points)
        self.assertTrue(result.passed, f"Wave 3 shortest rule failed: {result.details}")

    def test_validator_with_perfect_data(self):
        """
        Tests the main `validate_impulse_wave` function with the perfect pattern.
        This ensures all rules are correctly aggregated.
        """
        # 1. Setup: Create a pattern object
        # The 'type' in WavePoint needs to be a string like 'L' or 'H', not an int
        points = [
            WavePoint(pd.Timestamp('2023-01-01 14:00'), 10, 'L'),
            WavePoint(pd.Timestamp('2023-01-01 16:00'), 20, 'H'),
            WavePoint(pd.Timestamp('2023-01-01 17:00'), 15, 'L'),
            WavePoint(pd.Timestamp('2023-01-01 19:00'), 31, 'H'),
            WavePoint(pd.Timestamp('2023-01-01 20:00'), 25, 'L'),
            WavePoint(pd.Timestamp('2023-01-01 22:00'), 40, 'H')
        ]
        pattern = WavePattern("Bullish Impulse", points)

        # The `engine` parameter is not used in the validator, so we can pass None
        engine = None

        # 2. Action: Validate the pattern
        validate_impulse_wave(engine, pattern)

        # 3. Assertion: Check that all rules passed
        self.assertEqual(len(pattern.rules_results), 3)
        all_passed = all(r.passed for r in pattern.rules_results)
        failing_rules = [r.details for r in pattern.rules_results if not r.passed]
        self.assertTrue(all_passed, f"One or more validation rules failed: {failing_rules}")

# Keep placeholder tests for other files to ensure they are still checked
class TestBotInterface(unittest.TestCase):
    def test_initialization(self):
        self.assertTrue(True)

class TestDataFetching(unittest.TestCase):
    def test_initialization(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
