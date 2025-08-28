import csv
import os
from datetime import datetime
from typing import Dict, Any

LOG_FILE = 'trade_history.csv'
FIELDNAMES = [
    'log_timestamp', 'trade_id', 'symbol', 'pattern_type',
    'entry_price', 'stop_loss', 'initial_targets',
    'rr_ratio', 'confidence_score',
    'outcome', 'outcome_timestamp'
]

def log_trade(trade: Dict[str, Any], outcome: str):
    """
    Logs the details of a completed trade to a CSV file.

    Args:
        trade: The trade object dictionary.
        outcome: A string describing the outcome (e.g., 'SL_HIT', 'TP_FINAL').
    """
    file_exists = os.path.isfile(LOG_FILE)

    try:
        with open(LOG_FILE, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)

            if not file_exists:
                writer.writeheader()

            log_entry = {
                'log_timestamp': datetime.now().isoformat(),
                'trade_id': trade.get('id'),
                'symbol': trade.get('symbol'),
                'pattern_type': trade.get('pattern_type'),
                'entry_price': trade.get('entry'),
                'stop_loss': trade.get('stop_loss'),
                'initial_targets': str(trade.get('targets', [])),
                'rr_ratio': trade.get('rr_ratio'),
                'confidence_score': trade.get('confidence_score'),
                'outcome': outcome,
                'outcome_timestamp': datetime.now().isoformat()
            }
            writer.writerow(log_entry)
            print(f"SUCCESS: Logged completed trade {trade.get('id')} with outcome {outcome}.")

    except IOError as e:
        print(f"ERROR: Could not write to trade log file {LOG_FILE}: {e}")
