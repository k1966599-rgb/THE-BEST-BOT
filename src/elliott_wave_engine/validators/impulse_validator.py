from src.elliott_wave_engine.wave_structure import WavePattern
from src.elliott_wave_engine.rules import (
    wave_2_retrace_rule,
    wave_4_overlap_rule,
    wave_3_shortest_rule,
    wave_3_extension_rule,
    wave_4_retrace_rule,
    wave_3_momentum_rule,
    wave_5_divergence_rule,
    wave_5_truncation_rule,
    rule_of_alternation,
    wave_2_4_time_similarity_rule
)

def validate_impulse_wave(engine, pattern: WavePattern):
    """
    Validates a 5-wave pattern against the cardinal rules of an impulse wave
    by calling centralized rule functions.
    """
    if len(pattern.points) != 6:
        return

    # Add results from the three main impulse wave rules by directly appending
    # to the list. This is a more defensive approach.
    pattern.rules_results.append(wave_2_retrace_rule(pattern.points))
    pattern.rules_results.append(wave_4_overlap_rule(pattern.points))
    pattern.rules_results.append(wave_3_shortest_rule(pattern.points))


def score_impulse_wave_guidelines(engine, pattern: WavePattern):
    """
    Scores an impulse wave based on common guidelines by calling centralized
    rule functions, including new momentum and divergence checks.
    """
    if len(pattern.points) != 6:
        return

    # Add results from common guidelines by directly appending.
    pattern.guidelines_results.append(wave_3_extension_rule(pattern.points))
    pattern.guidelines_results.append(wave_4_retrace_rule(pattern.points))

    # Add results from new momentum-based guidelines
    # These require the historical data with indicators, which is available in the engine
    pattern.guidelines_results.append(wave_3_momentum_rule(pattern.points, engine.data))
    pattern.guidelines_results.append(wave_5_divergence_rule(pattern.points, engine.data))

    # Add check for 5th wave truncation
    pattern.guidelines_results.append(wave_5_truncation_rule(pattern.points))

    # Add check for the Rule of Alternation
    pattern.guidelines_results.append(rule_of_alternation(pattern.points))

    # Add check for time similarity between waves 2 and 4
    pattern.guidelines_results.append(wave_2_4_time_similarity_rule(pattern.points))
