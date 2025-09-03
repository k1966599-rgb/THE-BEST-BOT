"""
ملف التكوين السريع للبوت
قم بتعديل القيم أدناه حسب احتياجاتك
"""
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# إعدادات التداول والتحليل
TRADING_CONFIG = {
    # معرف المنصة على ccxt (e.g., 'okx', 'binance', 'kucoin')
    'EXCHANGE_ID': 'okx',
    'DEFAULT_SYMBOL': 'BTC/USDT',
    'PERIOD': '1y',
    'INTERVAL': '1d',
    'ACCOUNT_BALANCE': 10000,
    'MAX_RISK_PER_TRADE': 0.02,
    'MAX_PORTFOLIO_RISK': 0.06
}

# إعدادات المنصة (يتم تحميلها من .env)
EXCHANGE_CONFIG = {
    'API_KEY': os.getenv('EXCHANGE_API_KEY', ''),
    'API_SECRET': os.getenv('EXCHANGE_API_SECRET', ''),
    'PASSWORD': os.getenv('EXCHANGE_API_PASSWORD', ''),
    'SANDBOX_MODE': os.getenv('SANDBOX_MODE', 'False').lower() in ('true', '1', 't')
}

# إعدادات التليجرام (يتم تحميلها من .env)
TELEGRAM_CONFIG = {
    'BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
    'AUTO_SEND': os.getenv('TELEGRAM_AUTO_SEND', 'False').lower() in ('true', '1', 't')
}

# إعدادات التحليل المتقدمة
ANALYSIS_CONFIG = {
    'LOOKBACK_PERIOD': 50,
    'PIVOT_WINDOW': 5,
    'MIN_PATTERN_BARS': 10,
    'LEVEL_TOLERANCE': 0.002,
    'ATR_MULTIPLIER': 2.0,
    'ATR_PERIOD': 14
}

# قائمة المراقبة
WATCHLIST = [
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'DOGE/USDT',
    'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'BNB/USDT', 'MATIC/USDT'
]

# إعدادات الحفظ والتقارير
OUTPUT_CONFIG = {
    'OUTPUT_FOLDER': 'analysis_reports',
    'FILENAME_FORMAT': '{symbol}_analysis_{timestamp}',
    'SAVE_JSON': True,
    'SAVE_TXT': True,
    'SAVE_CHARTS': False
}

def get_config():
    """استرجاع جميع الإعدادات"""
    return {
        'trading': TRADING_CONFIG,
        'exchange': EXCHANGE_CONFIG,
        'telegram': TELEGRAM_CONFIG,
        'analysis': ANALYSIS_CONFIG,
        'watchlist': WATCHLIST,
        'output': OUTPUT_CONFIG
    }

def print_current_config():
    # ... (the rest of the file remains the same)
    pass

if __name__ == "__main__":
    print_current_config()
