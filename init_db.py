import sqlite3
import datetime

DB_NAME = "trading_data.db"

def initialize_database():
    """
    Creates the necessary database and tables for storing trade data and analysis
    based on the user's detailed specification.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("Creating 'trades' table...")
    # Main table for fundamental trade data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        symbol TEXT NOT NULL,
        action TEXT, -- BUY/SELL
        entry_price REAL,
        exit_price REAL,
        quantity REAL,
        pnl REAL,
        pnl_percentage REAL,
        duration_minutes INTEGER,
        max_profit REAL,
        max_drawdown REAL,
        exit_reason TEXT -- TARGET/STOP/SIGNAL_CHANGE/MANUAL
    );
    ''')

    print("Creating 'trade_timeframes' table...")
    # Table to store the analysis context for each timeframe related to a trade
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_timeframes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        timeframe TEXT NOT NULL,
        wave_pattern TEXT,
        wave_strength REAL,
        trend_direction TEXT,
        reliability_score REAL,
        contributed_to_decision BOOLEAN,
        FOREIGN KEY (trade_id) REFERENCES trades(id)
    );
    ''')

    print("Creating 'trade_indicators' table...")
    # Table to store the state of key indicators at the time of a trade decision
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        timeframe TEXT NOT NULL,
        indicator_name TEXT NOT NULL,
        indicator_category TEXT,
        value_at_entry REAL,
        signal_at_entry TEXT,
        strength_at_entry REAL,
        contributed_to_decision BOOLEAN,
        weight_used REAL,
        FOREIGN KEY (trade_id) REFERENCES trades(id)
    );
    ''')

    # This table was also in the user's spec, for future use in Stage 2
    print("Creating 'indicator_performance' table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS indicator_performance (
        indicator_name TEXT,
        timeframe TEXT,
        total_signals INTEGER DEFAULT 0,
        successful_signals INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0,
        avg_profit_when_right REAL,
        avg_loss_when_wrong REAL,
        best_market_condition TEXT,
        worst_market_condition TEXT,
        last_updated DATETIME,
        PRIMARY KEY (indicator_name, timeframe)
    );
    ''')

    conn.commit()
    conn.close()
    print("Database and tables initialized successfully.")

if __name__ == "__main__":
    initialize_database()
