import pandas as pd
import json
from typing import Dict, Any, Optional

# Import the new V2 Engine and the ZigZag pivot finder
from src.elliott_wave_engine.engine_v2 import ElliottWaveEngineV2
from src.elliott_wave_engine.indicators.zigzag import zigzag_pivots
from src.data.bybit_client import BybitClient
from src.trading.trade_proposer import define_trade_setup # We will re-purpose this later

class AnalysisManager:
    """
    Orchestrates analysis using the new ElliottWaveEngineV2.
    This is a simplified manager that focuses on a single timeframe analysis
    as a starting point, per the user's new engine design.
    """
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.engine = ElliottWaveEngineV2(debug_mode=True)
        self.client = BybitClient()
        self.context: Dict[str, Any] = {
            "symbol": symbol,
            "final_trade_setup": None,
            "final_decision": "REJECT",
            "decision_path": []
        }

    def _fetch_data_and_pivots(self, timeframe: str) -> Optional[Dict]:
        """Fetches data and calculates pivots using ZigZag."""
        self.context['decision_path'].append(f"Fetch({timeframe})")

        # 1. Fetch Data
        historical_data = self.client.get_historical_data(self.symbol, timeframe, total_candles=500)
        if historical_data is None or historical_data.empty:
            self.context['decision_path'].append("->REJECT:NoData")
            return None

        # 2. Calculate Pivots using ZigZag
        self.context['decision_path'].append("Pivots(ZigZag)")
        threshold_map = {'1h': 0.02, '4h': 0.03, '15m': 0.015, '5m': 0.01, '3m': 0.01}
        threshold = threshold_map.get(timeframe, 0.015)

        highs = historical_data['high'].to_numpy()
        lows = historical_data['low'].to_numpy()
        pivots = zigzag_pivots(highs, lows, threshold=threshold)

        if not pivots:
            self.context['decision_path'].append("->REJECT:NoPivots")
            return None

        self.context['decision_path'].append(f"->OK:{len(pivots)}pivots")
        return {"data": historical_data, "pivots": pivots}

    def run_analysis(self, timeframe: str = '15m'):
        """
        Runs a single-timeframe analysis using the new V2 engine.
        This replaces the complex hierarchical analysis for now.
        """
        print(f"--- Starting V2 Analysis for {self.symbol} on {timeframe} ---")

        # 1. Get data and pivots
        data_and_pivots = self._fetch_data_and_pivots(timeframe)
        if not data_and_pivots:
            print(f"Analysis failed for {self.symbol}: Could not get data or pivots.")
            return

        # 2. Run the new engine
        self.context['decision_path'].append("EngineV2.Analyze")
        price_data = data_and_pivots['data']['close'].to_numpy()
        pivots = data_and_pivots['pivots']
        analysis_result = self.engine.analyze(price_data, pivots)

        self.context['analysis_result'] = analysis_result

        # 3. Propose a trade based on the results
        self.context['decision_path'].append("ProposeTrade")
        # Note: The new engine's output is a list of dicts, not WaveScenario objects.
        # We pass the raw analysis result to the proposer, which will need to be adapted.
        trade_setup = define_trade_setup(analysis_result, data_and_pivots['data'])

        if trade_setup and trade_setup.get('type') in ['LONG', 'SHORT']:
            self.context['final_trade_setup'] = trade_setup
            self.context['final_decision'] = "DEFER" # Defer until price is in zone
            self.context['decision_path'].append(f"->OK:TradeSetupGenerated({trade_setup['reason']})")
        else:
            self.context['decision_path'].append("->REJECT:NoTradeableSetup")

        print(f"--- Analysis for {self.symbol} Complete. ---")
        print("Path: " + " ".join(self.context['decision_path']))
        print(f"Final Decision: {self.context['final_decision']}")
        return
