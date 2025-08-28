import pandas as pd
import traceback
from typing import List, Tuple
import pandas as pd
from src.data.bybit_client import BybitClient
from src.elliott_wave_engine.core.engine import ElliottWaveEngine
from src.elliott_wave_engine.core.wave_structure import WaveScenario

def m5_scalp_strategy(symbol: str, strict: bool = True) -> Tuple[List[WaveScenario], pd.DataFrame]:
    """
    Fetches 5-minute data, runs analysis, and returns the scenarios and the data with indicators.
    """
    try:
        client = BybitClient()
        historical_data = client.get_historical_data(symbol, "5")

        if historical_data is None or historical_data.empty:
            print(f"Could not fetch historical data for {symbol} on 5m timeframe.")
            return [], pd.DataFrame()

        # Instantiate the engine and run the analysis
        engine = ElliottWaveEngine(symbol, "5", historical_data)
        scenarios = engine.run_analysis(strict=strict)

        # Return the scenarios and the data used for analysis (which now includes indicators)
        return scenarios, engine.data
    except Exception as e:
        print(f"An error occurred in M5 strategy for {symbol}: {e}")
        traceback.print_exc()
        return [], pd.DataFrame() # Return empty tuple on error
