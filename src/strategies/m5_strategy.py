"""
استراتيجية سكالبينج M5
"""
import logging
import pandas as pd
from typing import Dict, List, Optional
import numpy as np

try:
    from src.elliott_wave_engine.core.engine import ElliottWaveEngine
except ImportError:
    ElliottWaveEngine = None

def m5_scalp_strategy(historical_data: pd.DataFrame, symbol: str = "BTCUSDT") -> Dict:
    """
    استراتيجية سكالبينج 5 دقائق
    """
    logger = logging.getLogger(__name__)

    try:
        if historical_data is None or len(historical_data) < 50:
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': 'بيانات غير كافية للتحليل',
                'symbol': symbol,
                'timeframe': '5m',
                'analysis': {}
            }

        # تحليل الاتجاه السريع
        trend_analysis = analyze_m15_trend(historical_data)

        # مؤشرات التداول السريع
        scalp_indicators = calculate_scalp_indicators(historical_data)

        # إشارات الدخول والخروج
        entry_signals = find_entry_signals(historical_data, scalp_indicators)

        # Elliott Wave Analysis (اختياري)
        wave_analysis = {}
        if ElliottWaveEngine:
            try:
                engine = ElliottWaveEngine()
                wave_analysis = engine.analyze_waves(historical_data)
            except Exception as e:
                logger.warning(f"Elliott Wave analysis failed: {e}")
                wave_analysis = {'error': str(e)}

        # تحديد الإشارة النهائية
        final_signal = determine_m15_signal(trend_analysis, scalp_indicators, entry_signals)

        return {
            'action': final_signal['action'],
            'confidence': final_signal['confidence'],
            'reason': final_signal['reason'],
            'symbol': symbol,
            'timeframe': '5m',
            'analysis': {
                'trend': trend_analysis,
                'indicators': scalp_indicators,
                'entry_signals': entry_signals,
                'wave_analysis': wave_analysis,
                'price_levels': calculate_price_levels(historical_data)
            }
        }

    except Exception as e:
        logger.error(f"خطأ في استراتيجية M5 لـ {symbol}: {e}")
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reason': f'خطأ في التحليل: {str(e)}',
            'symbol': symbol,
            'timeframe': '5m',
            'analysis': {}
        }

def analyze_m15_trend(data: pd.DataFrame) -> Dict:
    """تحليل الاتجاه السريع لـ M5"""
    try:
        # Moving averages سريعة
        data['ema9'] = data['close'].ewm(span=9).mean()
        data['ema21'] = data['close'].ewm(span=21).mean()
        data['sma50'] = data['close'].rolling(50).mean()

        current_price = data['close'].iloc[-1]
        ema9 = data['ema9'].iloc[-1]
        ema21 = data['ema21'].iloc[-1]

        if current_price > ema9 > ema21:
            trend = 'صاعد قوي'
            strength = 0.8
        elif current_price > ema9:
            trend = 'صاعد'
            strength = 0.6
        elif current_price < ema9 < ema21:
            trend = 'هابط قوي'
            strength = 0.8
        elif current_price < ema9:
            trend = 'هابط'
            strength = 0.6
        else:
            trend = 'جانبي'
            strength = 0.3

        return {
            'direction': trend,
            'strength': strength,
            'current_price': current_price,
            'ema9': ema9,
            'ema21': ema21
        }

    except Exception as e:
        return {'direction': 'غير محدد', 'strength': 0.0, 'error': str(e)}

def calculate_scalp_indicators(data: pd.DataFrame) -> Dict:
    """حساب مؤشرات السكالبينج"""
    try:
        # RSI سريع
        rsi = calculate_rsi(data['close'], period=14)

        # Stochastic
        stoch_k, stoch_d = calculate_stochastic(data)

        # Williams %R
        williams_r = calculate_williams_r(data, period=14)

        # Volume analysis
        volume_sma = data['volume'].rolling(20).mean()
        volume_ratio = data['volume'].iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1

        return {
            'rsi': {
                'value': rsi.iloc[-1] if not rsi.empty else 50,
                'signal': 'buy' if rsi.iloc[-1] < 30 else 'sell' if rsi.iloc[-1] > 70 else 'neutral'
            },
            'stochastic': {
                'k': stoch_k.iloc[-1] if not stoch_k.empty else 50,
                'd': stoch_d.iloc[-1] if not stoch_d.empty else 50,
                'signal': 'buy' if stoch_k.iloc[-1] < 20 else 'sell' if stoch_k.iloc[-1] > 80 else 'neutral'
            },
            'williams_r': {
                'value': williams_r.iloc[-1] if not williams_r.empty else -50,
                'signal': 'buy' if williams_r.iloc[-1] < -80 else 'sell' if williams_r.iloc[-1] > -20 else 'neutral'
            },
            'volume': {
                'ratio': volume_ratio,
                'signal': 'strong' if volume_ratio > 1.5 else 'weak' if volume_ratio < 0.5 else 'normal'
            }
        }

    except Exception as e:
        return {'error': str(e)}

def find_entry_signals(data: pd.DataFrame, indicators: Dict) -> List[Dict]:
    """العثور على إشارات الدخول"""
    signals = []

    try:
        # إشارة RSI
        if indicators.get('rsi', {}).get('signal') == 'buy':
            signals.append({
                'type': 'buy',
                'indicator': 'RSI',
                'strength': 0.7,
                'reason': 'RSI oversold'
            })
        elif indicators.get('rsi', {}).get('signal') == 'sell':
            signals.append({
                'type': 'sell',
                'indicator': 'RSI',
                'strength': 0.7,
                'reason': 'RSI overbought'
            })

        # إشارة Stochastic
        stoch_signal = indicators.get('stochastic', {}).get('signal')
        if stoch_signal == 'buy':
            signals.append({
                'type': 'buy',
                'indicator': 'Stochastic',
                'strength': 0.6,
                'reason': 'Stochastic oversold'
            })
        elif stoch_signal == 'sell':
            signals.append({
                'type': 'sell',
                'indicator': 'Stochastic',
                'strength': 0.6,
                'reason': 'Stochastic overbought'
            })

        return signals

    except Exception as e:
        return [{'error': str(e)}]

def determine_m15_signal(trend: Dict, indicators: Dict, signals: List[Dict]) -> Dict:
    """تحديد الإشارة النهائية لـ M5"""
    try:
        buy_signals = len([s for s in signals if s.get('type') == 'buy'])
        sell_signals = len([s for s in signals if s.get('type') == 'sell'])

        # حساب القوة الإجمالية
        total_strength = sum([s.get('strength', 0) for s in signals])

        if buy_signals > sell_signals and trend.get('direction') in ['صاعد', 'صاعد قوي']:
            return {
                'action': 'BUY',
                'confidence': min(0.9, 0.5 + (buy_signals * 0.2) + (trend.get('strength', 0) * 0.3)),
                'reason': f'اتجاه صاعد + {buy_signals} إشارة شراء'
            }
        elif sell_signals > buy_signals and trend.get('direction') in ['هابط', 'هابط قوي']:
            return {
                'action': 'SELL',
                'confidence': min(0.9, 0.5 + (sell_signals * 0.2) + (trend.get('strength', 0) * 0.3)),
                'reason': f'اتجاه هابط + {sell_signals} إشارة بيع'
            }
        else:
            return {
                'action': 'HOLD',
                'confidence': 0.3,
                'reason': 'إشارات متضاربة أو ضعيفة'
            }

    except Exception as e:
        return {
            'action': 'HOLD',
            'confidence': 0.0,
            'reason': f'خطأ في التحليل: {str(e)}'
        }

def calculate_price_levels(data: pd.DataFrame) -> Dict:
    """حساب مستويات الأسعار المهمة"""
    try:
        recent_high = data['high'].tail(20).max()
        recent_low = data['low'].tail(20).min()
        current_price = data['close'].iloc[-1]

        # مستويات Pivot
        pivot = (recent_high + recent_low + current_price) / 3
        r1 = 2 * pivot - recent_low
        s1 = 2 * pivot - recent_high

        return {
            'pivot': pivot,
            'resistance': r1,
            'support': s1,
            'recent_high': recent_high,
            'recent_low': recent_low
        }

    except Exception as e:
        return {'error': str(e)}

# المؤشرات الفنية
def calculate_rsi(prices, period=14):
    """حساب RSI"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series([50] * len(prices))

def calculate_stochastic(data, k_period=14, d_period=3):
    """حساب Stochastic"""
    try:
        low_min = data['low'].rolling(window=k_period).min()
        high_max = data['high'].rolling(window=k_period).max()
        k_percent = 100 * ((data['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    except:
        zeros = pd.Series([50] * len(data))
        return zeros, zeros

def calculate_williams_r(data, period=14):
    """حساب Williams %R"""
    try:
        high_max = data['high'].rolling(window=period).max()
        low_min = data['low'].rolling(window=period).min()
        williams_r = -100 * ((high_max - data['close']) / (high_max - low_min))
        return williams_r
    except:
        return pd.Series([-50] * len(data))
