import sqlite3
from datetime import datetime
import json
from typing import Dict, Any

DB_NAME = "trading_data.db"

class TradingLearningSystem:
    """
    A system for logging detailed trade data for future analysis and learning.
    This is the foundation for the self-optimizing system requested by the user.
    """
    def __init__(self, db_path: str = DB_NAME):
        """
        Initializes the learning system with the path to the SQLite database.
        """
        self.db_path = db_path
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensures the database connection can be made."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except sqlite3.Error as e:
            print(f"FATAL: Could not connect to database at {self.db_path}: {e}")
            raise

    def log_closed_trade(self, trade_data: Dict[str, Any], closed_trade_event: Dict[str, Any]):
        """
        Logs a completed trade to the database.
        This version focuses on capturing the core trade outcome data.
        The full context (indicators, multi-timeframe analysis) will be added
        once the data collection pipeline is integrated.
        """
        print(f"INFO: Logging closed trade for {trade_data.get('symbol')} to learning database.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # --- Prepare data for the 'trades' table ---
            entry_price = trade_data.get('entry')
            exit_price = closed_trade_event.get('price') # The price at which the trade was closed (SL or TP)
            pnl = None
            pnl_percentage = None

            if entry_price and exit_price:
                # Assuming a LONG trade for now
                pnl = exit_price - entry_price
                pnl_percentage = (pnl / entry_price) * 100 if entry_price != 0 else 0

            cursor.execute('''
            INSERT INTO trades (
                timestamp, symbol, action, entry_price, exit_price, pnl, pnl_percentage, exit_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                trade_data.get('symbol'),
                'LONG', # Assuming all trades are LONG for now as per strategy
                entry_price,
                exit_price,
                pnl,
                pnl_percentage,
                closed_trade_event.get('event') # e.g., 'SL_HIT', 'TP_HIT'
            ))

            trade_id = cursor.lastrowid
            print(f"SUCCESS: Logged trade with ID {trade_id} to 'trades' table.")

            # --- Placeholder for logging to related tables ---
            # In the next step, we will plumb the analysis_context through
            # and uncomment/implement the following:
            # self._log_timeframe_data(cursor, trade_id, trade_data.get('analysis_context'))
            # self._log_indicator_data(cursor, trade_id, trade_data.get('analysis_context'))

            conn.commit()
        except sqlite3.Error as e:
            print(f"ERROR: Failed to log trade to database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def _log_timeframe_data(self, cursor: sqlite3.Cursor, trade_id: int, context: Dict[str, Any]):
        """Placeholder for logging timeframe-specific analysis data."""
        # This will be implemented in the integration step.
        print(f"INFO: Placeholder for logging timeframe data for trade {trade_id}.")
        pass

    def _log_indicator_data(self, cursor: sqlite3.Cursor, trade_id: int, context: Dict[str, Any]):
        """Placeholder for logging indicator data."""
        # This will be implemented in the integration step.
        print(f"INFO: Placeholder for logging indicator data for trade {trade_id}.")
        pass
