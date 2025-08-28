import pandas as pd
from typing import Dict, Any, Optional, List

# Import strategy functions
from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.h1_strategy import h1_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import define_trade_setup
from src.elliott_wave_engine.core.wave_structure import WaveScenario

class AnalysisManager:
    """
    Orchestrates a hierarchical, multi-timeframe analysis based on Elliott Wave theory.
    """
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.context: Dict[str, Any] = {
            "symbol": symbol,
            "final_trade_setup": None,
            "final_decision": "REJECT",
            "decision_path": []
        }

    def _run_phase(self, phase_name: str, tf_str: str, strategy_func, htf_context: Optional[dict] = None) -> bool:
        """Generic function to run a phase of the analysis."""
        self.context['decision_path'].append(f"P({tf_str})")
        scenarios, data = strategy_func(self.symbol)
        if not scenarios:
            self.context['decision_path'].append("->REJECT:NoPatterns")
            return False

        self.context[f'{tf_str}_scenarios'] = scenarios
        self.context[f'{tf_str}_data'] = data
        ltf_type = scenarios[0].primary_pattern.pattern_type.lower()
        self.context['decision_path'].append(f"->OK:{ltf_type[:5]}")

        if htf_context:
            htf_type = htf_context['scenarios'][0].primary_pattern.pattern_type.lower()
            if "impulse" in htf_type and any(c in ltf_type for c in ["zigzag", "flat", "triangle"]):
                self.context['decision_path'].append("->MATCH:HTF_Imp/LTF_Corr")
                return True
            elif any(c in htf_type for c in ["zigzag", "flat", "triangle"]) and "impulse" in ltf_type:
                self.context['decision_path'].append("->MATCH:HTF_Corr/LTF_Imp")
                return True
            self.context['decision_path'].append("->REJECT:NoAlign")
            return False
        return True

    def _generate_trade_setup(self) -> bool:
        """Generates the trade parameters from the 15m analysis."""
        self.context['decision_path'].append("GenerateSetup")
        scenarios: List[WaveScenario] = self.context['15m_scenarios']
        data: pd.DataFrame = self.context['15m_data']
        trade_setup = define_trade_setup(scenarios, data)

        if not trade_setup or trade_setup.get('type') != 'LONG':
            self.context['decision_path'].append("->REJECT:NoLongSetup")
            return False

        self.context['final_trade_setup'] = trade_setup
        self.context['decision_path'].append("->OK:SetupGenerated")
        return True

    def _confirm_entry_conditions(self) -> None:
        """Final confirmation using 5m and 3m data."""
        self.context['decision_path'].append("Confirm(5m/3m)")
        trade_setup = self.context['final_trade_setup']

        # Phase 4: 5m Confirmation (e.g., breakout)
        _, data_5m = m5_scalp_strategy(self.symbol)
        if data_5m.empty:
            self.context['decision_path'].append("->DEFER:No5m_data")
            self.context['final_decision'] = "DEFER"
            return

        # Simple confirmation: last 5m candle must be bullish
        last_5m_candle = data_5m.iloc[-1]
        if last_5m_candle['close'] <= last_5m_candle['open']:
            self.context['decision_path'].append("->DEFER:5m_not_bullish")
            self.context['final_decision'] = "DEFER"
            return

        self.context['decision_path'].append("->OK:5m_bullish")

        # Phase 5: 3m Entry Trigger (Price in zone + Indicators)
        _, data_3m = m3_scalp_strategy(self.symbol)
        if data_3m.empty:
            self.context['decision_path'].append("->DEFER:No3m_data")
            self.context['final_decision'] = "DEFER"
            return

        current_price = data_3m['close'].iloc[-1]
        entry_zone = trade_setup['entry_zone']

        if not (entry_zone[1] <= current_price <= entry_zone[0]):
            self.context['decision_path'].append(f"->DEFER:Price_not_in_zone")
            self.context['final_decision'] = "DEFER"
            return

        latest_indicators = data_3m.iloc[-1]
        stoch_k = latest_indicators.get('STOCHRSIk_14_14_3_3', 50)
        macd_hist = latest_indicators.get('MACDh_12_26_9', 0)
        if stoch_k > latest_indicators.get('STOCHRSId_14_14_3_3', 50) and macd_hist > 0:
            self.context['decision_path'].append("->ACCEPT")
            self.context['final_decision'] = "ACCEPT"
        else:
            self.context['decision_path'].append("->DEFER:Indicators_weak")
            self.context['final_decision'] = "DEFER"

    def run_hierarchical_analysis(self) -> None:
        """Executes the full, top-down analysis pipeline."""
        print(f"--- Starting Hierarchical Analysis for {self.symbol} ---")
        if not self._run_phase("Strategic", "4h", h4_long_term_strategy): return

        h4_context = {"scenarios": self.context['4h_scenarios']}
        if not self._run_phase("Tactical", "1h", h1_strategy, h4_context): return

        h1_context = {"scenarios": self.context['1h_scenarios']}
        if not self._run_phase("Tactical", "15m", m15_scalp_strategy, h1_context): return

        if not self._generate_trade_setup(): return

        self._confirm_entry_conditions()

        print(f"--- Analysis for {self.symbol} Complete. ---")
        print("Path: " + " ".join(self.context['decision_path']))
        print(f"Final Decision: {self.context['final_decision']}")
        return
