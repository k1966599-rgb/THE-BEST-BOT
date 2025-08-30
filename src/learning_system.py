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
        Logs a completed trade and its full analysis context to the database.
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
                closed_trade_event.get('event')
            ))

            trade_id = cursor.lastrowid
            print(f"SUCCESS: Logged trade with ID {trade_id} to 'trades' table.")

            # --- Log to related tables using the analysis snapshot ---
            analysis_snapshot = trade_data.get('analysis_snapshot', {})
            if analysis_snapshot:
                self._log_timeframe_data(cursor, trade_id, analysis_snapshot)
                self._log_indicator_data(cursor, trade_id, analysis_snapshot)
            else:
                print("WARNING: No analysis_snapshot found in trade_data. Detailed logging will be skipped.")

            conn.commit()

            # After committing, update the long-term performance stats in a separate transaction
            if pnl is not None:
                self.update_performance_stats(trade_data, pnl)
        except sqlite3.Error as e:
            print(f"ERROR: Failed to log trade to database: {e}")
            conn.rollback()
        finally:
            conn.close()

    def run_learning_cycle(self):
        """
        Runs a full learning cycle: analyze performance and update weights.
        """
        print("--- Running a new learning cycle ---")
        # 1. Analyze performance of past trades
        analysis_results = self.analyze_performance(days=30)

        # 2. Update weights based on analysis
        if analysis_results:
            self.update_weights(analysis_results)

        print("--- Learning cycle complete ---")

    def load_weights(self) -> Dict[str, Any]:
        """Loads the strategy weights from the JSON file."""
        try:
            with open("strategy_weights.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("WARNING: strategy_weights.json not found or invalid. Using default weights.")
            # Return default weights if file doesn't exist or is corrupt
            return {
                "timeframes": {"4h": 1.0, "1h": 1.0, "15m": 1.0},
                "last_updated": "2025-01-01T00:00:00"
            }

    def save_weights(self, weights: Dict[str, Any]):
        """Saves the strategy weights to the JSON file."""
        print("INFO: Saving updated strategy weights.")
        try:
            weights['last_updated'] = datetime.now().isoformat()
            with open("strategy_weights.json", "w") as f:
                json.dump(weights, f, indent=4)
            print("SUCCESS: Weights saved.")
        except IOError as e:
            print(f"ERROR: Could not save weights to strategy_weights.json: {e}")

    def update_weights(self, analysis_results: Dict[str, Any]):
        """
        Updates the strategy weights based on performance analysis.
        This is a simple implementation based on the user's logic.
        """
        print("INFO: Updating weights based on performance analysis.")
        weights = self.load_weights()

        # --- Update Timeframe Weights ---
        tf_performance = analysis_results.get('timeframe_performance', {})
        for tf, data in tf_performance.items():
            if tf in weights['timeframes']:
                # Only adjust if there's a minimum number of trades to avoid noise
                if data.get('trade_count', 0) > 5:
                    success_rate = data.get('success_rate', 0.5)
                    if success_rate > 0.6: # If success rate is good, increase weight
                        weights['timeframes'][tf] *= 1.05
                    elif success_rate < 0.4: # If success rate is poor, decrease weight
                        weights['timeframes'][tf] *= 0.95

                    # Clamp weights to a reasonable range, e.g., [0.5, 2.0]
                    weights['timeframes'][tf] = max(0.5, min(weights['timeframes'][tf], 2.0))

        # --- Placeholder for updating indicator/pattern weights ---

        self.save_weights(weights)

    def _log_timeframe_data(self, cursor: sqlite3.Cursor, trade_id: int, snapshot: Dict[str, Any]):
        """Logs timeframe-specific analysis data for a given trade."""
        print(f"INFO: Logging timeframe data for trade {trade_id}.")
        timeframe_data_to_log = []
        for tf in ['4h', '1h', '15m']:
            if f'{tf}_pattern' in snapshot:
                pattern_info = snapshot[f'{tf}_pattern']
                timeframe_data_to_log.append((
                    trade_id,
                    tf,
                    pattern_info.get('pattern_type'),
                    pattern_info.get('confidence_score'), # wave_strength
                    None, # trend_direction - placeholder
                    pattern_info.get('confidence_score'), # reliability_score
                    True # contributed_to_decision - placeholder
                ))

        if timeframe_data_to_log:
            cursor.executemany('''
            INSERT INTO trade_timeframes
            (trade_id, timeframe, wave_pattern, wave_strength, trend_direction, reliability_score, contributed_to_decision)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', timeframe_data_to_log)
            print(f"SUCCESS: Logged {len(timeframe_data_to_log)} timeframe records for trade {trade_id}.")


    def _log_indicator_data(self, cursor: sqlite3.Cursor, trade_id: int, snapshot: Dict[str, Any]):
        """Logs indicator data for a given trade."""
        print(f"INFO: Logging indicator data for trade {trade_id}.")
        indicator_data_to_log = []

        # Define which indicators to log from the snapshot
        indicators_to_log = {
            'rsi': 'momentum', 'macd_hist': 'momentum', 'stoch_rsi_k': 'momentum',
            'volume': 'volume'
        }

        for tf in ['4h', '1h', '15m']:
            if f'{tf}_indicators' in snapshot:
                indicators = snapshot[f'{tf}_indicators']
                for indicator_key, category in indicators_to_log.items():
                    # A bit of key mapping to handle different naming conventions
                    # e.g., MACDh_12_26_9 -> macd_hist
                    value_key = next((k for k in indicators.keys() if indicator_key in k.lower()), None)
                    if value_key and value_key in indicators:
                        indicator_data_to_log.append((
                            trade_id,
                            tf,
                            value_key, # indicator_name
                            category,
                            indicators[value_key], # value_at_entry
                            None, # signal_at_entry - placeholder
                            None, # strength_at_entry - placeholder
                            True, # contributed_to_decision - placeholder
                            None  # weight_used - placeholder
                        ))

        if indicator_data_to_log:
            cursor.executemany('''
            INSERT INTO trade_indicators
            (trade_id, timeframe, indicator_name, indicator_category, value_at_entry, signal_at_entry, strength_at_entry, contributed_to_decision, weight_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', indicator_data_to_log)
            print(f"SUCCESS: Logged {len(indicator_data_to_log)} indicator records for trade {trade_id}.")

    def analyze_performance(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyzes the performance of different trading factors over a given period.
        """
        print(f"INFO: Analyzing performance for the last {days} days.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        analysis_results = {}

        try:
            # --- Analyze Timeframe Performance ---
            cursor.execute('''
            SELECT
                tf.timeframe,
                AVG(CASE WHEN t.pnl > 0 THEN 1.0 ELSE 0.0 END) as success_rate,
                COUNT(t.id) as total_trades
            FROM trades t
            JOIN trade_timeframes tf ON t.id = tf.trade_id
            WHERE t.timestamp >= datetime('now', ?)
            GROUP BY tf.timeframe
            ''', (f'-{days} days',))

            tf_performance = cursor.fetchall()
            analysis_results['timeframe_performance'] = {row[0]: {'success_rate': row[1], 'trade_count': row[2]} for row in tf_performance}
            print(f"INFO: Timeframe analysis complete: {analysis_results['timeframe_performance']}")

            # --- Placeholder for Indicator Performance Analysis ---
            # This can be expanded later as per the user's full specification.

        except sqlite3.Error as e:
            print(f"ERROR: Failed to analyze performance: {e}")
        finally:
            conn.close()

        return analysis_results

    def update_performance_stats(self, trade_data: Dict[str, Any], pnl: float):
        """
        Updates the long-term performance tracking tables, like indicator_performance.
        """
        print("INFO: Updating long-term performance stats.")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            is_success = 1 if pnl > 0 else 0
            snapshot = trade_data.get('analysis_snapshot', {})

            for tf in ['4h', '1h', '15m']:
                if f'{tf}_indicators' in snapshot:
                    indicators = snapshot[f'{tf}_indicators']
                    for indicator_name, value in indicators.items():
                        # Use INSERT OR IGNORE to avoid errors if the row already exists
                        cursor.execute('''
                        INSERT OR IGNORE INTO indicator_performance (indicator_name, timeframe) VALUES (?, ?)
                        ''', (indicator_name, tf))

                        # Update the stats
                        cursor.execute('''
                        UPDATE indicator_performance
                        SET total_signals = total_signals + 1,
                            successful_signals = successful_signals + ?,
                            last_updated = ?
                        WHERE indicator_name = ? AND timeframe = ?
                        ''', (is_success, datetime.now(), indicator_name, tf))

            # Recalculate success rate after update
            cursor.execute('''
            UPDATE indicator_performance
            SET success_rate = CAST(successful_signals AS REAL) / total_signals
            WHERE total_signals > 0
            ''')

            conn.commit()
            print("SUCCESS: Updated performance stats.")
        except sqlite3.Error as e:
            print(f"ERROR: Failed to update performance stats: {e}")
            conn.rollback()
        finally:
            conn.close()
