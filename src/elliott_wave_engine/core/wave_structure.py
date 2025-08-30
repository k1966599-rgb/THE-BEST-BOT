from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum
import numpy as np

class WaveType(Enum):
    """أنواع الموجات"""
    IMPULSE = "impulse"
    CORRECTIVE = "corrective"
    DIAGONAL = "diagonal"
    TRIANGLE = "triangle"
    COMPLEX = "complex"

class WavePattern(Enum):
    """أنماط الموجات المحددة"""
    IMPULSE_12345 = "impulse_12345"
    ZIGZAG_ABC = "zigzag_abc"
    FLAT_ABC = "flat_abc"
    TRIANGLE_ABCDE = "triangle_abcde"
    DOUBLE_THREE = "double_three"
    TRIPLE_THREE = "triple_three"
    DIAGONAL_ENDING = "diagonal_ending"
    DIAGONAL_LEADING = "diagonal_leading"

@dataclass
class WavePoint:
    """نقطة في الموجة"""
    index: int
    price: float
    type: str  # 'peak' or 'trough'
    timestamp: Optional[float] = None
    volume: Optional[float] = None

@dataclass
class Wave:
    """موجة واحدة"""
    wave_number: int  # 1, 2, 3, 4, 5 or A, B, C
    start_point: WavePoint
    end_point: WavePoint
    wave_type: WaveType
    subwaves: Optional[List['Wave']] = None
    retracement: Optional[float] = None
    extension: Optional[float] = None

@dataclass
class WaveScenario:
    """سيناريو كامل للموجات"""
    pattern: WavePattern
    waves: List[Wave]
    confidence: float
    direction: str  # 'bullish' or 'bearish'
    current_wave: Optional[int] = None
    next_targets: Optional[List[float]] = None
    invalidation_level: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى dictionary للتسلسل"""
        return {
            'pattern': self.pattern.value,
            'confidence': self.confidence,
            'direction': self.direction,
            'current_wave': self.current_wave,
            'next_targets': self.next_targets,
            'invalidation_level': self.invalidation_level,
            'wave_count': len(self.waves)
        }

    def get_current_position(self) -> str:
        """الحصول على الموقع الحالي في النمط"""
        if self.current_wave:
            if self.pattern in [WavePattern.IMPULSE_12345]:
                return f"Wave {self.current_wave} of 5"
            elif self.pattern in [WavePattern.ZIGZAG_ABC, WavePattern.FLAT_ABC]:
                wave_labels = ['A', 'B', 'C']
                if self.current_wave <= 3:
                    return f"Wave {wave_labels[self.current_wave-1]} of ABC"
        return "Unknown position"

    def get_trade_recommendation(self) -> Dict[str, Any]:
        """الحصول على توصية التداول"""
        recommendations = []

        # توصيات بناءً على الموجة الحالية
        if self.pattern == WavePattern.IMPULSE_12345:
            if self.current_wave == 2:
                recommendations.append({
                    'action': 'BUY' if self.direction == 'bullish' else 'SELL',
                    'reason': 'End of Wave 2 correction',
                    'target': 'Wave 3 completion',
                    'confidence': self.confidence * 0.9
                })
            elif self.current_wave == 4:
                recommendations.append({
                    'action': 'BUY' if self.direction == 'bullish' else 'SELL',
                    'reason': 'End of Wave 4 correction',
                    'target': 'Wave 5 completion',
                    'confidence': self.confidence * 0.8
                })
            elif self.current_wave == 5:
                recommendations.append({
                    'action': 'SELL' if self.direction == 'bullish' else 'BUY',
                    'reason': 'Wave 5 completion expected',
                    'target': 'ABC correction',
                    'confidence': self.confidence * 0.85
                })

        elif self.pattern in [WavePattern.ZIGZAG_ABC, WavePattern.FLAT_ABC]:
            if self.current_wave == 3:  # Wave C
                recommendations.append({
                    'action': 'BUY' if self.direction == 'bearish' else 'SELL',
                    'reason': 'ABC correction completing',
                    'target': 'New impulse wave',
                    'confidence': self.confidence * 0.75
                })

        return recommendations[0] if recommendations else {'action': 'WAIT', 'reason': 'No clear setup'}

@dataclass
class WaveAnalysisResult:
    """نتيجة تحليل الموجات"""
    scenarios: List[WaveScenario]
    best_scenario: Optional[WaveScenario]
    alternative_count: int
    analysis_timestamp: float
    timeframe: str
    symbol: str

    def get_summary(self) -> str:
        """ملخص التحليل"""
        if not self.best_scenario:
            return "No clear wave pattern identified"

        return (f"Best scenario: {self.best_scenario.pattern.value} "
                f"({self.best_scenario.confidence:.1%} confidence) - "
                f"{self.best_scenario.get_current_position()}")

# فئات إضافية قد تكون مطلوبة
@dataclass
class FibonacciLevel:
    """مستوى فيبوناتشي"""
    level: float
    price: float
    type: str  # 'retracement' or 'extension'

@dataclass
class WaveRules:
    """قواعد موجات إليوت"""
    wave2_max_retracement: float = 0.99
    wave3_min_extension: float = 1.0
    wave4_no_overlap: bool = True
    wave5_min_length: float = 0.382

    def validate_impulse(self, waves: List[Wave]) -> bool:
        """التحقق من صحة الموجة الدافعة"""
        if len(waves) < 5:
            return False

        # Rule 1: Wave 2 cannot retrace more than 100% of Wave 1
        if waves[1].retracement and waves[1].retracement > self.wave2_max_retracement:
            return False

        # Rule 2: Wave 3 cannot be the shortest
        wave_lengths = [abs(w.end_point.price - w.start_point.price) for w in waves[:5:2]]
        if wave_lengths[1] < wave_lengths[0] and wave_lengths[1] < wave_lengths[2]:
            return False

        # Rule 3: Wave 4 should not overlap Wave 1 (في الأسواق التقليدية)
        # يمكن تجاهل هذه القاعدة في العملات الرقمية

        return True

# دوال مساعدة
def create_wave_from_points(start: Dict, end: Dict, wave_number: int) -> Wave:
    """إنشاء موجة من نقطتين"""
    start_point = WavePoint(
        index=start.get('index', 0),
        price=start.get('price', 0),
        type=start.get('type', 'trough')
    )
    end_point = WavePoint(
        index=end.get('index', 0),
        price=end.get('price', 0),
        type=end.get('type', 'peak')
    )

    return Wave(
        wave_number=wave_number,
        start_point=start_point,
        end_point=end_point,
        wave_type=WaveType.IMPULSE if wave_number in [1, 3, 5] else WaveType.CORRECTIVE
    )

def calculate_fibonacci_levels(high: float, low: float, is_retracement: bool = True) -> List[FibonacciLevel]:
    """حساب مستويات فيبوناتشي"""
    levels = [0.236, 0.382, 0.5, 0.618, 0.786] if is_retracement else [1.0, 1.272, 1.618, 2.0, 2.618]
    diff = high - low

    fib_levels = []
    for level in levels:
        if is_retracement:
            price = high - (diff * level)
        else:
            price = low + (diff * level)

        fib_levels.append(FibonacciLevel(
            level=level,
            price=price,
            type='retracement' if is_retracement else 'extension'
        ))

    return fib_levels
