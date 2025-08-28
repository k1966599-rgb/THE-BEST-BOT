from typing import List, Dict, Any, Generator, Optional
from collections import defaultdict
import pandas as pd

from .wave_structure import WavePoint, WavePattern, ComplexWavePattern, WaveScenario
from ..indicators.pivots import find_pivots
from ..indicators.momentum import calculate_rsi, calculate_macd

# Import pattern logic from the new modular structure
from ..patterns.impulse import generate_impulse_waves, validate_impulse_wave
from ..patterns.zigzag import generate_zigzag_waves, validate_zigzag_wave
from ..patterns.flat import generate_flat_waves, validate_flat_wave
from ..patterns.triangle import generate_triangle_waves, validate_triangle_wave
from ..patterns.diagonal import generate_diagonal_waves, validate_diagonal_wave
from ..patterns.wxy import generate_wxy_waves, validate_wxy_wave


class ElliottWaveEngine:
    def __init__(self, symbol: str, timeframe: str, historical_data: pd.DataFrame, context: dict = None, depth: int = 0):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = historical_data
        self.context = context
        self.depth = depth
        self.wave_counts: List[WaveScenario] = []
        self._prepare_data()
        self.pivots = self._find_pivots()

    def _prepare_data(self):
        self.data['rsi'] = calculate_rsi(self.data)
        macd_df = calculate_macd(self.data)
        new_macd_cols = [col for col in macd_df.columns if col not in self.data.columns]
        self.data = self.data.join(macd_df[new_macd_cols])
        self.data.ta.atr(append=True)

    def _find_pivots(self) -> List[Dict[str, Any]]:
        avg_price = self.data['close'].mean()
        # Further increased sensitivity for lower timeframes to find more patterns.
        prominence_map = {
            '4h':  avg_price * 0.005,   # 0.5%
            '240': avg_price * 0.005,
            '1h':  avg_price * 0.002,   # 0.2%
            '60':  avg_price * 0.002,
            '15m': avg_price * 0.0006,  # 0.06% (very sensitive)
            '15':  avg_price * 0.0006,
            '5m':  avg_price * 0.0004,  # 0.04% (hyper sensitive)
            '5':   avg_price * 0.0004,
            '3m':  avg_price * 0.0002,  # 0.02% (extremely sensitive)
            '3':   avg_price * 0.0002,
        }
        prominence = prominence_map.get(str(self.timeframe), avg_price * 0.002)
        return find_pivots(self.data, prominence=prominence)

    def run_analysis(self, strict: bool = True) -> List[WaveScenario]:
        all_valid_patterns = self._find_all_patterns(strict=strict)
        scenarios = self._group_competing_patterns(all_valid_patterns)
        scenarios.sort(key=lambda s: s.primary_pattern.confidence_score, reverse=True)
        self.wave_counts = scenarios
        return self.wave_counts

    def _find_all_patterns(self, strict: bool = True) -> List[WavePattern]:
        valid_patterns = []
        pattern_generators = {
            "Impulse": generate_impulse_waves,
            "Zigzag": generate_zigzag_waves,
            "Flat": generate_flat_waves,
            "Triangle": generate_triangle_waves,
            "Diagonal": generate_diagonal_waves,
        }
        pattern_validators = {
            "Impulse": validate_impulse_wave,
            "Zigzag": validate_zigzag_wave,
            "Flat": validate_flat_wave,
            "Triangle": validate_triangle_wave,
            "Diagonal": validate_diagonal_wave,
        }
        for name, generator_func in pattern_generators.items():
            for p in generator_func(self.pivots):
                validator_func = pattern_validators.get(name)
                if validator_func:
                    validator_func(self, p) # This now handles rules AND guidelines

                # The validator function populates rules_results. We check if all cardinal rules passed.
                if all(r.passed for r in p.rules_results):
                    if strict:
                        # The validator also populates guidelines_results. Now we can calculate the score.
                        p.calculate_confidence()
                    valid_patterns.append(p)

        # WXY waves are generated from simple correctives
        simple_correctives = [p for p in valid_patterns if "Zigzag" in p.pattern_type or "Flat" in p.pattern_type]
        for p in generate_wxy_waves(self.pivots, simple_correctives):
            validate_wxy_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    p.calculate_confidence()
                valid_patterns.append(p)

        return valid_patterns

    def _group_competing_patterns(self, patterns: List[WavePattern]) -> List[WaveScenario]:
        groups = defaultdict(list)
        for p in patterns: groups[p.points[-1].time].append(p)
        scenarios = []
        for _, competing_patterns in groups.items():
            if competing_patterns:
                competing_patterns.sort(key=lambda p: p.confidence_score, reverse=True)
                scenarios.append(WaveScenario(competing_patterns[0], competing_patterns[1:]))
        return scenarios
