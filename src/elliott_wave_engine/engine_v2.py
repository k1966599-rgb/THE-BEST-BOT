import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class WaveType(Enum):
    IMPULSE = "impulse"
    CORRECTIVE = "corrective"
    DIAGONAL = "diagonal"
    TRIANGLE = "triangle"

@dataclass
class WavePoint:
    index: int
    price: float
    type: str  # 'peak' or 'trough'
    timestamp: Optional[float] = None

@dataclass
class Wave:
    points: List[WavePoint]
    wave_type: WaveType
    confidence: float
    subwaves: Optional[List] = None

class ElliottWaveEngineV2:
    """
    محرك محسّن وموثوق لتحليل موجات إليوت
    """
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.min_wave_size = 0.001  # 0.1% حركة سعرية كحد أدنى
        self.patterns_found = []

    def analyze(self, price_data: np.ndarray, pivots: List[Dict]) -> Dict:
        """
        التحليل الرئيسي - مبسط وفعال
        """
        if self.debug_mode:
            print(f"Starting analysis with {len(pivots)} pivots")

        # 1. تحويل النقاط المحورية إلى صيغة موحدة
        wave_points = self._convert_pivots_to_points(pivots, price_data)

        if len(wave_points) < 3:
            if self.debug_mode:
                print("Not enough points for analysis")
            return {"patterns": [], "status": "insufficient_data"}

        # 2. البحث عن الأنماط بطريقة متدرجة (من البسيط للمعقد)
        patterns = []

        # المستوى 1: البحث عن أنماط ABC البسيطة (3 نقاط)
        abc_patterns = self._find_abc_patterns(wave_points)
        patterns.extend(abc_patterns)

        # المستوى 2: البحث عن موجات دافعة 5 نقاط
        if len(wave_points) >= 5:
            impulse_patterns = self._find_impulse_patterns(wave_points)
            patterns.extend(impulse_patterns)

        # المستوى 3: البحث عن أنماط معقدة
        if len(wave_points) >= 7:
            complex_patterns = self._find_complex_patterns(wave_points)
            patterns.extend(complex_patterns)

        # 3. تقييم وترتيب الأنماط
        scored_patterns = self._score_and_rank_patterns(patterns)

        if self.debug_mode:
            print(f"Found {len(scored_patterns)} patterns")
            for i, pattern in enumerate(scored_patterns[:3]):
                print(f"Pattern {i+1}: {pattern['type']} - Confidence: {pattern['confidence']:.2%}")

        return {
            "patterns": scored_patterns,
            "status": "success",
            "wave_count": len(wave_points),
            "best_pattern": scored_patterns[0] if scored_patterns else None
        }

    def _convert_pivots_to_points(self, pivots: List[Dict], price_data: np.ndarray) -> List[WavePoint]:
        """
        تحويل النقاط المحورية إلى صيغة موحدة
        """
        points = []

        for i, pivot in enumerate(pivots):
            # التعامل مع صيغ مختلفة للبيانات
            if isinstance(pivot, dict):
                index = pivot.get('index', pivot.get('idx', i))
                price = pivot.get('price', pivot.get('value', 0))
                pivot_type = pivot.get('type', 'peak' if i % 2 == 0 else 'trough')
            elif isinstance(pivot, (list, tuple)):
                index = pivot[0] if len(pivot) > 0 else i
                price = pivot[1] if len(pivot) > 1 else 0
                pivot_type = 'peak' if i % 2 == 0 else 'trough'
            else:
                # افتراض أن القيمة هي السعر مباشرة
                index = i
                price = float(pivot)
                pivot_type = 'peak' if i % 2 == 0 else 'trough'

            points.append(WavePoint(
                index=index,
                price=float(price),
                type=pivot_type
            ))

        return points

    def _find_abc_patterns(self, points: List[WavePoint]) -> List[Dict]:
        """
        البحث عن أنماط ABC (3 موجات تصحيحية)
        """
        patterns = []

        for i in range(len(points) - 2):
            a = points[i]
            b = points[i + 1]
            c = points[i + 2]

            # حساب النسب
            ab_move = abs(b.price - a.price)
            bc_move = abs(c.price - b.price)

            if ab_move == 0:
                continue

            bc_ratio = bc_move / ab_move

            # تحديد نوع النمط ABC
            pattern_type = None
            confidence = 0

            # Zigzag: 5-3-5 structure (BC = 0.618-1.0 of AB)
            if 0.5 <= bc_ratio <= 1.1:
                pattern_type = "ABC_Zigzag"
                confidence = 0.7 + (0.3 * (1 - abs(bc_ratio - 0.786)))

            # Flat: 3-3-5 structure (BC = 0.9-1.1 of AB)
            elif 0.85 <= bc_ratio <= 1.15:
                pattern_type = "ABC_Flat"
                confidence = 0.6 + (0.4 * (1 - abs(bc_ratio - 1.0)))

            # Irregular: BC > 1.0 of AB
            elif bc_ratio > 1.0:
                pattern_type = "ABC_Irregular"
                confidence = 0.5 + min(0.3, (bc_ratio - 1.0) * 0.5)

            if pattern_type:
                patterns.append({
                    'type': pattern_type,
                    'points': [a, b, c],
                    'start_index': a.index,
                    'end_index': c.index,
                    'confidence': min(confidence, 0.95),
                    'ratios': {'bc_to_ab': bc_ratio},
                    'direction': 'bullish' if c.price > a.price else 'bearish'
                })

        return patterns

    def _find_impulse_patterns(self, points: List[WavePoint]) -> List[Dict]:
        """
        البحث عن موجات دافعة (5 موجات)
        """
        patterns = []

        for i in range(len(points) - 4):
            wave_points = points[i:i+5]

            # استخراج الموجات
            w1_start, w1_end = wave_points[0], wave_points[1]
            w2_end = wave_points[2]
            w3_end = wave_points[3]
            w4_end = wave_points[4]

            # حساب أطوال الموجات
            w1_length = abs(w1_end.price - w1_start.price)
            w2_length = abs(w2_end.price - w1_end.price)
            w3_length = abs(w3_end.price - w2_end.price)
            w4_length = abs(w4_end.price - w3_end.price)

            if w1_length == 0:
                continue

            # التحقق من القواعد الأساسية
            rules_check = self._check_impulse_rules(wave_points)

            if rules_check['valid']:
                # حساب النسب
                w2_retrace = w2_length / w1_length if w1_length > 0 else 0
                w3_extension = w3_length / w1_length if w1_length > 0 else 0
                w4_retrace = w4_length / w3_length if w3_length > 0 else 0

                # حساب مستوى الثقة
                confidence = self._calculate_impulse_confidence(
                    w2_retrace, w3_extension, w4_retrace, rules_check
                )

                patterns.append({
                    'type': 'Impulse_12345',
                    'points': wave_points,
                    'start_index': wave_points[0].index,
                    'end_index': wave_points[-1].index,
                    'confidence': confidence,
                    'ratios': {
                        'wave2_retracement': w2_retrace,
                        'wave3_extension': w3_extension,
                        'wave4_retracement': w4_retrace
                    },
                    'direction': 'bullish' if wave_points[-1].price > wave_points[0].price else 'bearish',
                    'rules_check': rules_check
                })

        return patterns

    def _check_impulse_rules(self, points: List[WavePoint]) -> Dict:
        """
        التحقق من قواعد الموجات الدافعة
        """
        result = {
            'valid': True,
            'rules_passed': [],
            'rules_failed': []
        }

        # القاعدة 1: الموجة 2 لا تتجاوز بداية الموجة 1
        if len(points) >= 3:
            is_bullish = points[1].price > points[0].price
            if is_bullish:
                if points[2].price <= points[0].price:
                    result['rules_failed'].append('wave2_exceeds_wave1_start')
                    result['valid'] = False
                else:
                    result['rules_passed'].append('wave2_valid')
            else:
                if points[2].price >= points[0].price:
                    result['rules_failed'].append('wave2_exceeds_wave1_start')
                    result['valid'] = False
                else:
                    result['rules_passed'].append('wave2_valid')

        # القاعدة 2: الموجة 3 ليست الأقصر
        if len(points) >= 5:
            w1_length = abs(points[1].price - points[0].price)
            w3_length = abs(points[3].price - points[2].price)
            w5_length = abs(points[4].price - points[3].price) if len(points) > 4 else 0

            if w3_length < w1_length and w3_length < w5_length:
                result['rules_failed'].append('wave3_is_shortest')
                result['valid'] = False
            else:
                result['rules_passed'].append('wave3_not_shortest')

        # القاعدة 3: الموجة 4 لا تتداخل مع منطقة الموجة 1
        if len(points) >= 5:
            is_bullish = points[1].price > points[0].price
            if is_bullish:
                if points[4].price <= points[1].price:
                    result['rules_failed'].append('wave4_overlaps_wave1')
                    # هذه قاعدة مرنة في الأسواق الحديثة
                    # result['valid'] = False
                else:
                    result['rules_passed'].append('wave4_no_overlap')
            else:
                if points[4].price >= points[1].price:
                    result['rules_failed'].append('wave4_overlaps_wave1')
                    # result['valid'] = False
                else:
                    result['rules_passed'].append('wave4_no_overlap')

        return result

    def _calculate_impulse_confidence(self, w2_retrace, w3_extension, w4_retrace, rules_check):
        """
        حساب مستوى الثقة للموجة الدافعة
        """
        confidence = 0.5  # نقطة البداية

        # مكافأة للقواعد الصحيحة
        confidence += len(rules_check['rules_passed']) * 0.1
        confidence -= len(rules_check['rules_failed']) * 0.15

        # تقييم النسب المثالية
        # الموجة 2: عادة 0.382-0.618
        if 0.382 <= w2_retrace <= 0.618:
            confidence += 0.15
        elif 0.236 <= w2_retrace <= 0.786:
            confidence += 0.08

        # الموجة 3: عادة 1.618 أو أكثر
        if w3_extension >= 1.618:
            confidence += 0.2
        elif w3_extension >= 1.0:
            confidence += 0.1

        # الموجة 4: عادة 0.236-0.382
        if 0.236 <= w4_retrace <= 0.382:
            confidence += 0.1
        elif 0.382 <= w4_retrace <= 0.5:
            confidence += 0.05

        return min(max(confidence, 0.1), 0.95)

    def _find_complex_patterns(self, points: List[WavePoint]) -> List[Dict]:
        """
        البحث عن أنماط معقدة (مثلثات، أنماط مركبة)
        """
        patterns = []

        # البحث عن المثلثات (5 موجات متقاربة)
        for i in range(len(points) - 4):
            triangle_points = points[i:i+5]

            # حساب الميل للخطوط العلوية والسفلية
            upper_line = self._calculate_trendline([triangle_points[0], triangle_points[2], triangle_points[4]])
            lower_line = self._calculate_trendline([triangle_points[1], triangle_points[3]])

            if upper_line and lower_line:
                # تحديد نوع المثلث
                if abs(upper_line['slope']) < 0.01 and abs(lower_line['slope']) < 0.01:
                    triangle_type = "Symmetric_Triangle"
                    confidence = 0.7
                elif upper_line['slope'] * lower_line['slope'] < 0:
                    triangle_type = "Contracting_Triangle"
                    confidence = 0.8
                else:
                    triangle_type = "Expanding_Triangle"
                    confidence = 0.6

                patterns.append({
                    'type': triangle_type,
                    'points': triangle_points,
                    'start_index': triangle_points[0].index,
                    'end_index': triangle_points[-1].index,
                    'confidence': confidence,
                    'trendlines': {
                        'upper': upper_line,
                        'lower': lower_line
                    }
                })

        return patterns

    def _calculate_trendline(self, points: List[WavePoint]) -> Optional[Dict]:
        """
        حساب خط الاتجاه
        """
        if len(points) < 2:
            return None

        x = [p.index for p in points]
        y = [p.price for p in points]

        # Linear regression
        n = len(points)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i]**2 for i in range(n))

        denominator = n * sum_x2 - sum_x**2
        if denominator == 0:
            return None

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        return {
            'slope': slope,
            'intercept': intercept,
            'points': points
        }

    def _score_and_rank_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """
        تقييم وترتيب الأنماط حسب الجودة
        """
        for pattern in patterns:
            # حساب نقاط الجودة الإضافية
            quality_score = pattern['confidence']

            # مكافأة للأنماط الكاملة
            if 'Impulse' in pattern['type']:
                quality_score *= 1.2

            # مكافأة للأنماط ذات النسب المثالية
            if 'ratios' in pattern:
                ideal_ratios_count = sum(
                    1 for ratio in pattern['ratios'].values()
                    if 0.382 <= ratio <= 1.618
                )
                quality_score += ideal_ratios_count * 0.05

            pattern['quality_score'] = min(quality_score, 1.0)

        # ترتيب حسب الجودة
        patterns.sort(key=lambda x: x['quality_score'], reverse=True)

        return patterns
