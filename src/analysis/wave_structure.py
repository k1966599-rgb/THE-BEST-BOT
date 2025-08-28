from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class WavePoint:
    """Represents a single point in a wave pattern."""
    time: Any
    price: float
    type: str

@dataclass
class WaveRuleResult:
    """Represents the result of a single rule validation."""
    name: str
    passed: bool
    details: str = ""

@dataclass
class BaseWavePattern:
    """Represents a basic wave pattern identified by the analysis."""
    pattern_type: str
    points: List[WavePoint]
    rules_results: List[WaveRuleResult] = field(default_factory=list)
    confidence_score: float = 0.0
