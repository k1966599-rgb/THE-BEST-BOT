import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Any
import warnings

warnings.filterwarnings('ignore')

class TrendAnalysis:
    """وحدة تحليل الترندات الشاملة"""

    def __init__(self, df: pd.DataFrame, short_period: int = 20, medium_period: int = 50, long_period: int = 100):
        self.df = df.copy()
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period

    def identify_swing_points(self, window: int = 5) -> Dict[str, List]:
        """تحديد نقاط التأرجح (القمم والقيعان)"""
        highs = []
        lows = []

        # التأكد من أن لدينا بيانات كافية
        if len(self.df) <= window * 2:
            return {'highs': [], 'lows': []}

        for i in range(window, len(self.df) - window):
            # فحص القمة المحلية
            is_high = True
            for j in range(i - window, i + window + 1):
                if j != i and self.df['high'].iloc[j] >= self.df['high'].iloc[i]:
                    is_high = False
                    break
            if is_high:
                highs.append({
                    'index': i,
                    'price': self.df['high'].iloc[i],
                    'date': self.df.index[i]
                })

            # فحص القاع المحلي
            is_low = True
            for j in range(i - window, i + window + 1):
                if j != i and self.df['low'].iloc[j] <= self.df['low'].iloc[i]:
                    is_low = False
                    break
            if is_low:
                lows.append({
                    'index': i,
                    'price': self.df['low'].iloc[i],
                    'date': self.df.index[i]
                })

        return {'highs': highs, 'lows': lows}

    def detect_trend_lines(self) -> Dict[str, Any]:
        """كشف خطوط الاتجاه"""
        swing_points = self.identify_swing_points()
        highs = swing_points['highs']
        lows = swing_points['lows']

        trend_lines = {}

        if len(highs) >= 2:
            # خط الاتجاه العلوي (خط المقاومة)
            recent_highs = sorted(highs, key=lambda x: x['index'])[-3:]
            if len(recent_highs) >= 2:
                x_vals = [h['index'] for h in recent_highs]
                y_vals = [h['price'] for h in recent_highs]

                slope_high, intercept_high, r_value_high, _, _ = stats.linregress(x_vals, y_vals)

                current_index = len(self.df) - 1
                projected_resistance = slope_high * current_index + intercept_high

                trend_lines['resistance'] = {
                    'slope': slope_high,
                    'intercept': intercept_high,
                    'r_value': r_value_high,
                    'current_level': projected_resistance,
                    'strength': abs(r_value_high),
                    'direction': 'صاعد' if slope_high > 0 else 'هابط' if slope_high < 0 else 'عرضي'
                }

        if len(lows) >= 2:
            # خط الاتجاه السفلي (خط الدعم)
            recent_lows = sorted(lows, key=lambda x: x['index'])[-3:]
            if len(recent_lows) >= 2:
                x_vals = [l['index'] for l in recent_lows]
                y_vals = [l['price'] for l in recent_lows]

                slope_low, intercept_low, r_value_low, _, _ = stats.linregress(x_vals, y_vals)

                current_index = len(self.df) - 1
                projected_support = slope_low * current_index + intercept_low

                trend_lines['support'] = {
                    'slope': slope_low,
                    'intercept': intercept_low,
                    'r_value': r_value_low,
                    'current_level': projected_support,
                    'strength': abs(r_value_low),
                    'direction': 'صاعد' if slope_low > 0 else 'هابط' if slope_low < 0 else 'عرضي'
                }

        return trend_lines

    def analyze_trend_strength(self) -> Dict[str, Any]:
        """تحليل قوة الاتجاه"""
        current_price = self.df['close'].iloc[-1]

        sma_short = self.df['close'].rolling(window=self.short_period).mean().iloc[-1]
        sma_medium = self.df['close'].rolling(window=self.medium_period).mean().iloc[-1]
        sma_long = self.df['close'].rolling(window=self.long_period).mean().iloc[-1]

        short_trend = "صاعد" if current_price > sma_short else "هابط"
        medium_trend = "صاعد" if sma_short > sma_medium else "هابط"
        long_trend = "صاعد" if sma_medium > sma_long else "هابط"

        trend_strength_score = 0
        trend_alignment = []

        if current_price > sma_short: trend_strength_score += 1; trend_alignment.append("قصير المدى: صاعد")
        else: trend_strength_score -= 1; trend_alignment.append("قصير المدى: هابط")

        if sma_short > sma_medium: trend_strength_score += 1; trend_alignment.append("متوسط المدى: صاعد")
        else: trend_strength_score -= 1; trend_alignment.append("متوسط المدى: هابط")

        if sma_medium > sma_long: trend_strength_score += 1; trend_alignment.append("طويل المدى: صاعد")
        else: trend_strength_score -= 1; trend_alignment.append("طويل المدى: هابط")

        if trend_strength_score == 3: overall_trend = "اتجاه صاعد قوي جداً"
        elif trend_strength_score == 2: overall_trend = "اتجاه صاعد قوي"
        elif trend_strength_score == 1: overall_trend = "اتجاه صاعد ضعيف"
        elif trend_strength_score == 0: overall_trend = "اتجاه محايد/مختلط"
        elif trend_strength_score == -1: overall_trend = "اتجاه هابط ضعيف"
        elif trend_strength_score == -2: overall_trend = "اتجاه هابط قوي"
        else: overall_trend = "اتجاه هابط قوي جداً"

        recent_prices = self.df['close'].tail(self.short_period)
        x = np.arange(len(recent_prices))
        slope, _, r_value, _, _ = stats.linregress(x, recent_prices)
        angle = np.degrees(np.arctan(slope))

        return {
            'current_price': current_price, 'sma_short': sma_short, 'sma_medium': sma_medium,
            'sma_long': sma_long, 'short_trend': short_trend, 'medium_trend': medium_trend,
            'long_trend': long_trend, 'strength_score': trend_strength_score,
            'overall_trend': overall_trend, 'trend_alignment': trend_alignment,
            'trend_angle': angle, 'trend_r_value': r_value
        }

    def detect_trend_reversals(self) -> Dict[str, Any]:
        """كشف انعكاسات الاتجاه"""
        swing_points = self.identify_swing_points()
        highs = swing_points['highs']
        lows = swing_points['lows']

        reversal_signals = []
        reversal_score = 0

        if len(highs) >= 2 and len(lows) >= 2:
            recent_highs = sorted(highs, key=lambda x: x['index'])[-2:]
            recent_lows = sorted(lows, key=lambda x: x['index'])[-2:]

            if recent_highs[1]['price'] < recent_highs[0]['price']:
                reversal_signals.append("Lower High: قمة منخفضة - إشارة هبوط")
                reversal_score -= 1
            elif recent_highs[1]['price'] > recent_highs[0]['price']:
                reversal_signals.append("Higher High: قمة مرتفعة - إشارة صعود")
                reversal_score += 1

            if recent_lows[1]['price'] > recent_lows[0]['price']:
                reversal_signals.append("Higher Low: قاع مرتفع - إشارة صعود")
                reversal_score += 1
            elif recent_lows[1]['price'] < recent_lows[0]['price']:
                reversal_signals.append("Lower Low: قاع منخفض - إشارة هبوط")
                reversal_score -= 1

        if reversal_score >= 2: reversal_type = "انعكاس صعودي قوي محتمل"
        elif reversal_score >= 1: reversal_type = "انعكاس صعودي ضعيف محتمل"
        elif reversal_score <= -2: reversal_type = "انعكاس هبوطي قوي محتمل"
        elif reversal_score <= -1: reversal_type = "انعكاس هبوطي ضعيف محتمل"
        else: reversal_type = "لا يوجد إشارة انعكاس واضحة"

        return {
            'reversal_signals': reversal_signals, 'reversal_score': reversal_score,
            'reversal_type': reversal_type, 'recent_highs_count': len(highs),
            'recent_lows_count': len(lows)
        }

    def analyze_breakouts(self) -> Dict[str, Any]:
        """تحليل الكسرات (Breakouts)"""
        current_price = self.df['close'].iloc[-1]
        recent_high = self.df['high'].tail(self.short_period).max()
        recent_low = self.df['low'].tail(self.short_period).min()

        breakout_signals = []
        breakout_score = 0

        if current_price > recent_high:
            breakout_signals.append("كسر المقاومة - إشارة صعود")
            breakout_score += 2
        elif (recent_high - current_price) / current_price < 0.01:
            breakout_signals.append("قرب كسر المقاومة")
            breakout_score += 1

        if current_price < recent_low:
            breakout_signals.append("كسر الدعم - إشارة هبوط")
            breakout_score -= 2
        elif (current_price - recent_low) / current_price < 0.01:
            breakout_signals.append("قرب كسر الدعم")
            breakout_score -= 1

        volume_confirmation = False
        if 'volume' in self.df.columns:
            avg_volume = self.df['volume'].tail(self.short_period).mean()
            if self.df['volume'].iloc[-1] > avg_volume * 1.5:
                breakout_signals.append("تأكيد بالحجم - حجم عالي")
                volume_confirmation = True
                breakout_score += 1 if breakout_score > 0 else -1 if breakout_score < 0 else 0

        return {
            'resistance_level': recent_high, 'support_level': recent_low,
            'breakout_signals': breakout_signals, 'breakout_score': breakout_score,
            'volume_confirmation': volume_confirmation
        }

    def get_comprehensive_trend_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل للترندات"""
        trend_lines = self.detect_trend_lines()
        trend_strength = self.analyze_trend_strength()
        reversal_analysis = self.detect_trend_reversals()
        breakout_analysis = self.analyze_breakouts()

        total_score = (
            trend_strength.get('strength_score', 0) +
            reversal_analysis.get('reversal_score', 0) +
            breakout_analysis.get('breakout_score', 0)
        )

        if total_score >= 4: main_recommendation = "إشارة شراء قوية من تحليل الترند"
        elif total_score >= 2: main_recommendation = "إشارة شراء من تحليل الترند"
        elif total_score >= -1: main_recommendation = "محايد - مراقبة الترند"
        elif total_score >= -3: main_recommendation = "إشارة بيع من تحليل الترند"
        else: main_recommendation = "إشارة بيع قوية من تحليل الترند"

        return {
            'trend_lines': trend_lines, 'trend_strength': trend_strength,
            'reversal_analysis': reversal_analysis, 'breakout_analysis': breakout_analysis,
            'total_score': total_score, 'recommendation': main_recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
