"""
ملف التكوين السريع للبوت
قم بتعديل القيم أدناه حسب احتياجاتك
"""

# إعدادات التداول والتحليل
TRADING_CONFIG = {
    # معرف المنصة على ccxt (e.g., 'okx', 'binance', 'kucoin')
    'EXCHANGE_ID': 'okx',

    # الرمز الافتراضي للتحليل
    'DEFAULT_SYMBOL': 'BTC/USDT',

    # فترة البيانات المطلوبة (ccxt لا يستخدمها مباشرة، نحدد تاريخ البدء)
    'PERIOD': '1y',

    # فاصل زمني للشموع (e.g., '1m', '5m', '1h', '1d', '1w')
    'INTERVAL': '1d',

    # رصيد الحساب الافتراضي للتحليل
    'ACCOUNT_BALANCE': 10000,

    # نسبة المخاطرة القصوى لكل صفقة (2% = 0.02)
    'MAX_RISK_PER_TRADE': 0.02,

    # نسبة المخاطرة القصوى للمحفظة (6% = 0.06)
    'MAX_PORTFOLIO_RISK': 0.06
}

# إعدادات المنصة (اختياري، لـ private endpoints)
EXCHANGE_CONFIG = {
    'API_KEY': '',
    'API_SECRET': '',
    # بعض المنصات مثل OKX تتطلب كلمة مرور API
    'PASSWORD': '',
    # ccxt يمكنه استخدام وضع الاختبار لبعض المنصات
    'SANDBOX_MODE': False
}

# إعدادات التليجرام (اختيارية)
TELEGRAM_CONFIG = {
    'BOT_TOKEN': '',
    'CHAT_ID': '',
    'AUTO_SEND': False
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

# قائمة المراقبة (تأكد من أن الرموز بالتنسيق الصحيح للمنصة)
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
    """طباعة الإعدادات الحالية"""
    config = get_config()
    print("📋 الإعدادات الحالية:")
    print("="*40)
    for section_name, section_data in config.items():
        if section_name == 'watchlist':
            print(f"\n📊 {section_name.upper()}:")
            # تحويل اسم الرمز ليكون صالحًا كاسم ملف
            symbols_str = [s.replace('/', '_') for s in section_data]
            print(f"   {', '.join(symbols_str)}")
        else:
            print(f"\n⚙️ {section_name.upper()}:")
            for key, value in section_data.items():
                if key.upper() in ['BOT_TOKEN', 'CHAT_ID', 'API_KEY', 'API_SECRET', 'PASSWORD'] and value:
                    print(f"   {key}: {'*' * 10}")
                else:
                    print(f"   {key}: {value}")

if __name__ == "__main__":
    print_current_config()
