from src.elliott_wave_engine.wave_structure import WavePattern
from src.elliott_wave_engine.rules import (
    diagonal_wave_4_overlap_rule,
    diagonal_converging_rule,
    wave_3_shortest_rule,
    wave_2_retrace_rule
)

def validate_diagonal_wave(engine, pattern: WavePattern):
    """
    Validates a 5-wave pattern against the rules of a Diagonal Wave using centralized rules.
    """
    if len(pattern.points) != 6:
        return

    # --- Strict Rules ---
    # Rule 1: Wave 4 MUST overlap with Wave 1.
    pattern.add_rule_result(diagonal_wave_4_overlap_rule(pattern.points))

    # Rule 2: Wave 3 can still not be the shortest impulse wave.
    pattern.add_rule_result(wave_3_shortest_rule(pattern.points))

    # Rule 3: Wave 2 must not retrace beyond the start of Wave 1.
    pattern.add_rule_result(wave_2_retrace_rule(pattern.points))

    # --- Guidelines ---
    # Guideline 1: Check if the shape is converging (for a contracting diagonal).
    pattern.add_guideline_result(diagonal_converging_rule(pattern.points))

    # Note: Logic for expanding diagonals or differentiating between leading/ending
    # based on internal structure (5-3-5-3-5 vs 3-3-3-3-3) can be added later as an enhancement.
