from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class WavePoint:
    time: any
    price: float
    type: str
    idx: int # Add the candle index for time-based calculations

@dataclass
class WaveRuleResult:
    name: str
    passed: bool
    details: str = ""

@dataclass
class WavePattern:
    pattern_type: str
    points: List[WavePoint]
    rules_results: List[WaveRuleResult] = field(default_factory=list)
    guidelines_results: List[WaveRuleResult] = field(default_factory=list)
    confidence_score: float = 0.0
    characterization: Optional[str] = None

    def add_rule_result(self, result: WaveRuleResult):
        self.rules_results.append(result)

    def add_guideline_result(self, result: WaveRuleResult):
        self.guidelines_results.append(result)

    def calculate_confidence(self):
        guideline_weights = {
            "Guideline: W3 Extension": 25, "Guideline: W2 Retrace": 15, "Guideline: W4 Retrace": 10,
            "Guideline: Momentum Divergence": 30, "Guideline: Volume Pattern": 20,
            "Guideline: Alternation": 15, "Guideline: Fractal Validation": 40,
            "Guideline: Corrective Fractal Validation": 35, "Guideline: Time Relationship": 10,
        }
        if not all(r.passed for r in self.rules_results):
            self.confidence_score = 0.0
            return
        # Base score for passing all rules is now higher
        score = 60.0
        total_possible_guideline_score = sum(guideline_weights.values())
        if total_possible_guideline_score > 0:
            for g in self.guidelines_results:
                if g.passed:
                    weight = guideline_weights.get(g.name, 0)
                    # Guidelines now contribute to the remaining 40 points
                    score += (weight / total_possible_guideline_score) * 40.0
        self.confidence_score = min(score, 100.0)

@dataclass
class ComplexWavePattern(WavePattern):
    sub_patterns: List[WavePattern] = field(default_factory=list)

@dataclass
class WaveScenario:
    primary_pattern: WavePattern
    alternate_patterns: List[WavePattern] = field(default_factory=list)
    start_point: WavePoint = field(init=False)
    end_point: WavePoint = field(init=False)
    probabilities: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.start_point = self.primary_pattern.points[0]
        self.end_point = self.primary_pattern.points[-1]
        self._calculate_probabilities()

    def _calculate_probabilities(self):
        all_patterns = [self.primary_pattern] + self.alternate_patterns
        total_confidence = sum(p.confidence_score for p in all_patterns)
        if total_confidence == 0:
            prob = 100.0 / len(all_patterns) if all_patterns else 100.0
            for p in all_patterns: self.probabilities[p.pattern_type] = prob
        else:
            for p in all_patterns: self.probabilities[p.pattern_type] = (p.confidence_score / total_confidence) * 100.0
