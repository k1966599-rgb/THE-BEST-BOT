import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')

class SupportResistanceAnalysis:
    """وحدة تحليل الدعوم والمقاومة الشاملة، مع التركيز على مناطق العرض والطلب"""

    def __init__(self, df: pd.DataFrame, lookback_period: int = 100, tolerance: float = 0.01):
        self.df = df.copy()
        self.lookback_period = lookback_period
        self.tolerance = tolerance

    def find_all_levels(self) -> Dict[str, List[Dict]]:
        """تحديد جميع النقاط المحورية وتجميعها في مستويات أولية"""
        data = self.df.tail(self.lookback_period)
        if len(data) < 20: return {'supports': [], 'resistances': []}

        from scipy.signal import find_peaks
        # Corrected logic: highs are resistance, lows are support
        resistance_indices, _ = find_peaks(data['high'], prominence=data['high'].std() * 0.5)
        support_indices, _ = find_peaks(-data['low'], prominence=data['low'].std() * 0.5)

        supports = [{'price': data['low'].iloc[i], 'volume': data['volume'].iloc[i]} for i in support_indices]
        resistances = [{'price': data['high'].iloc[i], 'volume': data['volume'].iloc[i]} for i in resistance_indices]

        return {'supports': supports, 'resistances': resistances}

    def cluster_levels_to_zones(self, levels: List[Dict]) -> List[Dict]:
        """تجميع المستويات المتقاربة إلى مناطق (Zones)"""
        if not levels: return []

        sorted_levels = sorted(levels, key=lambda x: x['price'])
        zones = []
        current_zone = [sorted_levels[0]]

        for i in range(1, len(sorted_levels)):
            current_level = sorted_levels[i]
            last_level_in_zone = current_zone[-1]
            price_diff = abs(current_level['price'] - last_level_in_zone['price']) / last_level_in_zone['price']

            if price_diff <= self.tolerance:
                current_zone.append(current_level)
            else:
                # Corrected condition to include single-point zones
                if len(current_zone) >= 1:
                    zones.append(self.create_zone_from_cluster(current_zone))
                current_zone = [current_level]

        if len(current_zone) >= 1:
            zones.append(self.create_zone_from_cluster(current_zone))

        return zones

    def create_zone_from_cluster(self, cluster: List[Dict]) -> Dict:
        """إنشاء منطقة من عنقود من النقاط"""
        prices = [p['price'] for p in cluster]
        volumes = [p.get('volume', 0) for p in cluster]

        avg_price = np.mean(prices)
        # Create a small zone even for a single point
        zone_start = min(prices) * (1 - self.tolerance / 2)
        zone_end = max(prices) * (1 + self.tolerance / 2)
        total_touches = len(prices)
        total_volume = sum(volumes)

        strength = total_touches * (1 + (total_volume / self.df['volume'].mean()) / 10)

        return {
            'start': zone_start,
            'end': zone_end,
            'touches': total_touches,
            'strength': round(strength, 2),
            'avg_price': avg_price
        }

    def get_comprehensive_sr_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل لمناطق العرض والطلب"""
        levels = self.find_all_levels()

        support_zones = self.cluster_levels_to_zones(levels['supports'])
        resistance_zones = self.cluster_levels_to_zones(levels['resistances'])

        current_price = self.df['close'].iloc[-1]

        demand_zones = sorted([z for z in support_zones if z['end'] < current_price], key=lambda x: x['strength'], reverse=True)
        supply_zones = sorted([z for z in resistance_zones if z['start'] > current_price], key=lambda x: x['strength'], reverse=True)

        primary_demand_zone = demand_zones[0] if demand_zones else None
        primary_supply_zone = supply_zones[0] if supply_zones else None

        sr_score = 0
        if primary_demand_zone: sr_score += primary_demand_zone.get('strength', 0) / 5
        if primary_supply_zone: sr_score -= primary_supply_zone.get('strength', 0) / 5

        recommendation = "محايد"
        if sr_score > 1: recommendation = "مناطق الطلب قوية"
        elif sr_score < -1: recommendation = "مناطق العرض قوية"

        return {
            'primary_demand_zone': primary_demand_zone,
            'primary_supply_zone': primary_supply_zone,
            'all_demand_zones': demand_zones,
            'all_supply_zones': supply_zones,
            'sr_score': round(sr_score, 2),
            'recommendation': recommendation,
        }
