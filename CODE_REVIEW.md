# 📖 تقرير مراجعة الكود وتحليل البنية التحتية

مرحباً،

هذا التقرير يقدم تحليلاً شاملاً لمشروع بوت التداول الخاص بك. الهدف هو توفير رؤية واضحة حول الوضع الحالي للمشروع، تحديد نقاط القوة والضعف، وتقديم توصيات قابلة للتنفيذ لتحسين الكود، الأمان، وقابلية التوسع.

## 📝 الملخص التنفيذي

| الفئة | التقييم | ملاحظات سريعة |
| :--- | :--- | :--- |
| **الأمان (Security)** | 🔴 **حرج** | وجود مفاتيح API وبيانات حساسة مكشوفة في ملف الإعدادات. |
| **الموثوقية (Robustness)** | 🟠 **متوسط** | يعتمد على سكربت تشغيل بسيط، معالجة الأخطاء محدودة، وحالة البوت غير مستقرة عند إعادة التشغيل. |
| **قابلية الصيانة (Maintainability)** | 🟠 **متوسط** | الكود منظم بشكل جيد، ولكن وجود قيم ثابتة (Hardcoded) يجعله أقل مرونة. |
| **الاختبارات (Testing)** | 🟡 **يحتاج تحسين** | وجود بنية للاختبارات ولكنها غير مكتملة. |
| **التوثيق (Documentation)** | 🔴 **ضعيف جداً** | ملف `README.md` قديم جداً ولا يعكس وظائف البوت الحالية. |
| **التشغيل والنشر (Deployment)** | 🟠 **متوسط** | سكربت التشغيل `auto_bot.sh` فكرة جيدة ولكنه بحاجة لتحسينات كبيرة. |

---

## 1. تقييم البنية التحتية (Infrastructure Assessment)

هذا القسم يصف الهيكل العام للمشروع، التقنيات المستخدمة، وكيفية تفاعل المكونات المختلفة مع بعضها.

### أ. نظرة عامة على المشروع
- **الهدف:** بوت تداول آلي للعملات الرقمية يتصل بمنصة Telegram.
- **الاستراتيجية الأساسية:** يعتمد البوت على **تحليل موجات إليوت (Elliott Wave)** لتحديد الأنماط السعرية وفرص التداول المحتملة.
- **المنصة:** يتكامل مع منصة **Bybit** لجلب بيانات السوق (لا يوجد دليل على تنفيذ أوامر تداول حتى الآن).

### ب. التقنيات والمكتبات المستخدمة
- **لغة البرمجة:** Python 3.
- **واجهة البوت:** `python-telegram-bot` لإدارة التفاعل مع المستخدم عبر Telegram.
- **الاتصال بالمنصة:** `pybit` للتواصل مع Bybit API.
- **تحليل البيانات:** `pandas` لمعالجة السلاسل الزمنية للأسعار، `numpy` للعمليات الحسابية، و `pandas-ta` لإضافة المؤشرات الفنية.
- **الإعدادات:** `PyYAML` لقراءة ملف `config.yaml`.
- **الاختبارات:** `pytest` لإجراء الاختبارات على الكود.

### ج. هيكل الكود
الكود منظم بشكل جيد جداً في مجلد `src`، مما يسهل فهمه وصيانته. التقسيم كالتالي:
- `bot.py`: **نقطة الدخول الرئيسية** التي تشغل البوت.
- `config.yaml`: ملف الإعدادات المركزي الذي يحتوي على معلومات حساسة، قائمة الرموز، وإعدادات التحليل.
- `src/bot_interface`: مسؤول عن كل ما يتعلق بواجهة Telegram (الأوامر، الأزرار، تنسيق الرسائل).
- `src/data`: مسؤول عن جلب البيانات من منصة Bybit.
- `src/elliott_wave_engine`: **قلب النظام**، يحتوي على المنطق المعقد لتحليل وتحديد موجات إليوت.
- `src/strategies`: يجمع بين نتائج محرك موجات إليوت والمؤشرات الأخرى لتكوين استراتيجيات تداول محددة.
- `src/background_scanner.py`: يقوم بالمسح الدوري للعملات في الخلفية.
- `auto_bot.sh`: سكربت لتشغيل البوت ومراقبته وتحديثه تلقائياً من Git.

### د. آلية العمل (Execution Flow)
1.  **التشغيل:** يتم تشغيل البوت عبر سكربت `auto_bot.sh`. هذا السكربت يضمن أن البوت يعمل دائماً، وإذا توقف لأي سبب، يعيد تشغيله.
2.  **التحديث التلقائي:** يقوم السكربت أيضاً بسحب أي تحديثات جديدة من `git` وإعادة تشغيل البوت لتطبيقها.
3.  **بدء المسح:** بعد تشغيل البوت، يجب على المستخدم الضغط على زر "🟢 تشغيل البوت" في واجهة Telegram.
4.  **العمل في الخلفية:** عند الضغط على الزر، يبدأ `background_scanner.py` بالعمل في الخلفية، حيث يقوم بتحليل الرموز الموجودة في `config.yaml` بشكل دوري.
5.  **التنبيهات:** عند العثور على فرصة محتملة، يرسل البوت تنبيهاً إلى المستخدم عبر Telegram.
6.  **التحليل اليدوي:** يمكن للمستخدم أيضاً طلب تحليل فوري لعملة BTCUSDT على أطر زمنية مختلفة.

---

## 2. المشاكل الرئيسية ومجالات التحسين (Key Issues & Areas for Improvement)

هنا تفصيل لأهم المشاكل التي تم تحديدها، مرتبة حسب الأولوية والخطورة.

### 🔴 مشكلة حرجة: الأمان وإدارة البيانات الحساسة (Security & Secrets Management)
- **المشكلة:** مفتاح البوت الخاص بـ Telegram (`token`) مكتوب بشكل مباشر داخل ملف `config.yaml`. هذا يعتبر **ثغرة أمنية خطيرة جداً**. في حال تسرب الكود أو رفعه على مستودع عام (Public Repository)، سيتمكن أي شخص من السيطرة الكاملة على البوت الخاص بك.
- **الخطورة:** أي شخص يحصل على هذا المفتاح يمكنه التحكم في البوت، إرسال رسائل باسمه، وسرقة بيانات المستخدمين. الأمر نفسه ينطبق على مفاتيح API الخاصة بمنصة Bybit لو تمت إضافتها بنفس الطريقة، مما قد يؤدي إلى خسائر مالية.
- **التضارب:** يوجد تضارب في طريقة التعامل مع المفتاح. ملف `bot.py` يحاول قراءته من متغيرات البيئة (`os.getenv`), بينما هو موجود بشكل ثابت في `config.yaml`. هذا يسبب ارتباكاً ويجعل الكود غير متناسق.

### 🟠 مشكلة متوسطة: الموثوقية ومعالجة الأخطاء (Robustness & Error Handling)
- **فقدان الحالة عند إعادة التشغيل:** حالة تشغيل البوت (`is_running`) يتم تخزينها في الذاكرة المؤقتة (`context.bot_data`). سكربت `auto_bot.sh` يقوم بإعادة تشغيل البوت بشكل دوري، وعند كل إعادة تشغيل، **تُفقد هذه الحالة**. هذا يعني أن المسح التلقائي يتوقف ويجب على المستخدم الدخول إلى Telegram والضغط على "تشغيل البوت" مرة أخرى بعد كل تحديث.
- **غياب معالجة الأخطاء:** لا يوجد معالجة واضحة للأخطاء التي قد تحدث أثناء التشغيل، مثل:
    - انقطاع الاتصال بالإنترنت.
    - فشل الاتصال بـ API الخاص بـ Bybit (مثلاً، المنصة تحت الصيانة).
    - وجود خطأ في البيانات المستقبلة.
    هذه المشاكل قد تؤدي إلى توقف البوت بشكل كامل دون سابق إنذار.
- **غياب التسجيل المنظم (Logging):** الطريقة الحالية لتسجيل الأخطاء هي عبر تحويل كل المخرجات إلى ملف `bot.log`. هذه الطريقة غير عملية لتصحيح الأخطاء. المشروع بحاجة إلى نظام تسجيل منظم (structured logging) يسمح بتصنيف الرسائل (e.g., `INFO`, `WARNING`, `ERROR`) وتحديد مصدر الخطأ بدقة.

### 🟠 مشكلة متوسطة: التشغيل والنشر (Deployment)
- **سكربت التشغيل غير مستقر:** سكربت `auto_bot.sh` فكرة جيدة ولكنه يحتوي على عدة مشاكل:
    - **مسار ثابت (Hardcoded Path):** يستخدم المسار `/root/bot-telegram`، مما يجعله غير قابل للعمل على أي جهاز آخر.
    - **إيقاف غير آمن للعملية:** يستخدم `pkill -f "python3 bot.py"` لإيقاف البوت، وهي طريقة عنيفة وقد توقف عمليات أخرى بالخطأ إذا كانت أسماؤها متشابهة.
    - **لا يقوم بتثبيت الاعتماديات:** السكربت يقوم بسحب التحديثات من `git` ولكنه **لا يقوم بتثبيت الاعتماديات الجديدة** عبر `pip install -r requirements.txt`. إذا تم إضافة مكتبة جديدة، سيتوقف البوت عن العمل.

### 🟡 تحسين: قابلية الصيانة والمرونة (Maintainability & Flexibility)
- **قيم ثابتة (Hardcoded Values):** التحليل اليدوي في `handlers.py` مقتصر على عملة `BTCUSDT` فقط. إذا أردت تحليل عملة أخرى، ستحتاج إلى تعديل الكود مباشرة.
- **التوثيق ضعيف جداً:** ملف `README.md` لا يصف المشروع إطلاقاً وهو مخصص لمشروع أولي بسيط. هذا يجعل من الصعب على أي شخص (بما في ذلك أنت في المستقبل) فهم كيفية عمل المشروع وإعداده.
- **ميزات غير مكتملة:** وجود أزرار مثل "الصفقات النشطة" و "الاحصائيات" لا تعمل يترك انطباعاً بأن البوت غير مكتمل.

---

## 3. الملفات الموصى بإضافتها (Recommended Missing Files)

لتحسين المشروع وجعله أكثر احترافية وأماناً، أقترح إضافة الملفات التالية:

### أ. ملف `.env.example` لإدارة متغيرات البيئة
- **الغرض:** هذا الملف هو قالب (template) يوضح للمستخدم ما هي المتغيرات الحساسة التي يحتاجها المشروع ليعمل (مثل مفتاح Telegram ومفاتيح Bybit).
- **آلية العمل:**
    1. يتم إنشاء ملف `.env.example` ووضعه في المستودع.
    2. يقوم المستخدم بنسخ هذا الملف وتسميته `.env`.
    3. يضيف المستخدم قيمه الحقيقية في ملف `.env`.
    4. **الأهم:** يتم إضافة `.env` إلى ملف `.gitignore` لمنع رفعه إلى المستودع نهائياً.
- **الفائدة:** **حل المشكلة الأمنية الحرجة** المتعلقة بوجود المفاتيح في الكود.

### ب. ملف `Dockerfile` لتسهيل عملية النشر
- **الغرض:** هو ملف يحتوي على تعليمات لبناء "حاوية" (Container) تحتوي على كل ما يحتاجه البوت ليعمل: نظام التشغيل، نسخة بايثون، المكتبات، والكود نفسه.
- **الفائدة:**
    - **بيئة عمل موحدة:** يضمن أن البوت يعمل بنفس الطريقة على جهاز المطور وعلى الخادم.
    - **نشر بسيط وموثوق:** يجعل عملية النشر سهلة جداً عبر `docker-compose up`. لا حاجة لسكربت `auto_bot.sh` المعقد.
    - **عزل التطبيق:** يعمل البوت في بيئة معزولة تماماً عن باقي النظام.

### ج. ملف `ci.yml` للتكامل المستمر (CI/CD)
- **الغرض:** إعداد نظام آلي (عبر GitHub Actions) يقوم بفحص واختبار الكود تلقائياً عند كل تحديث.
- **آلية العمل:** يتم إنشاء ملف في المسار `.github/workflows/ci.yml` يحدد الخطوات التالية:
    1. فحص الكود عند كل `push`.
    2. تثبيت المكتبات المطلوبة.
    3. تشغيل الأدوات لفحص جودة الكود (linter).
    4. تشغيل الاختبارات الآلية (`pytest`).
- **الفائدة:**
    - **اكتشاف الأخطاء مبكراً:** يمنع دمج أي كود يحتوي على أخطاء في النسخة الرئيسية.
    - **ضمان جودة الكود:** يجبر الجميع على اتباع نفس معايير الجودة.

---

## 4. اقتراحات برمجية محددة (Specific Code-Level Suggestions)

هذا القسم يقدم حلولاً برمجية مقترحة للمشاكل التي نوقشت.

### أ. تحسين سكربت التشغيل `auto_bot.sh`
السكربت الحالي فعال ولكنه غير آمن. هذا إصدار محسن يعالج المشاكل الرئيسية:

```bash
#!/bin/bash

# Go to the script's directory, making it portable
cd "$(dirname "$0")"

PID_FILE="bot.pid"

start_bot() {
    echo "Starting bot..."
    # Run in background and save the PID
    nohup python3 bot.py > bot.log 2>&1 & echo $! > $PID_FILE
    echo "Bot started with PID $(cat $PID_FILE)."
}

stop_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        echo "Stopping bot with PID $PID..."
        kill $PID
        rm $PID_FILE
    else
        echo "Bot is not running (PID file not found)."
    fi
}

# Main loop
while true; do
    git fetch origin main
    # Check for updates
    if [ $(git rev-parse HEAD) != $(git rev-parse origin/main) ]; then
        echo "Update found. Pulling changes..."
        stop_bot
        git pull origin main
        echo "Installing/updating dependencies..."
        pip install -r requirements.txt # <-- Important: Install dependencies
        start_bot
        echo "Bot restarted with the latest update."
    fi

    # Check if bot is running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        # If the process with that PID does not exist
        if ! ps -p $PID > /dev/null; then
            echo "Bot seems to have crashed. Restarting..."
            rm $PID_FILE
            start_bot
        fi
    else
        # If PID file does not exist, bot is not running
        echo "Bot is not running. Starting..."
        start_bot
    fi

    sleep 10
done
```
**التحسينات:**
1.  **محمول:** لم يعد يعتمد على مسار ثابت.
2.  **إدارة العمليات عبر PID:** يستخدم ملف `bot.pid` لتخزين معرّف العملية، مما يجعل إيقافها آمناً ودقيقاً.
3.  **تثبيت الاعتماديات:** يقوم بتشغيل `pip install -r requirements.txt` بعد كل تحديث.

### ب. توحيد آلية تحميل الإعدادات
لحل مشكلة تضارب الإعدادات (بين `os.getenv` و `config.yaml`)، يمكنك تعديل `src/utils/config_loader.py` ليقوم بتحميل الإعدادات من كلا المصدرين ودمجها.

**مثال مقترح لـ `src/utils/config_loader.py`:**
```python
import os
import yaml
from dotenv import load_dotenv

# Load variables from .env file into environment variables
load_dotenv()

def load_config():
    """
    Loads configuration from config.yaml and environment variables.
    Environment variables override config.yaml settings.
    """
    # Load base configuration from YAML file
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Load secrets/overrides from environment variables
    # This is safer and aligns with best practices
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    bybit_api_key = os.getenv("BYBIT_API_KEY")
    bybit_api_secret = os.getenv("BYBIT_API_SECRET")

    if telegram_token:
        config['telegram']['token'] = telegram_token

    # You can add more overrides here
    if bybit_api_key:
        config['bybit']['api_key'] = bybit_api_key
    if bybit_api_secret:
        config['bybit']['api_secret'] = bybit_api_secret

    # Now, remove the hardcoded token from the config dictionary
    # to ensure it's only ever read from the environment
    if 'token' in config.get('telegram', {}):
        # If it was loaded from yaml, but we have an env var,
        # the env var has already overwritten it.
        # If we don't have an env var, we should raise an error
        # or handle it, but not leave a hardcoded secret.
        # For simplicity, we can just ensure it's not None.
        if not config['telegram']['token']:
             raise ValueError("Telegram token not found in environment variables or config.")

    return config

# You can create a single config instance to be imported across the app
config = load_config()
```
**التغييرات المطلوبة:**
1.  تثبيت `python-dotenv`: `pip install python-dotenv`.
2.  إنشاء ملف `.env.example` و `.env`.
3.  إزالة المفتاح الحساس من `config.yaml`.
4.  استيراد `config` من هذا الملف في جميع أنحاء التطبيق بدلاً من قراءة الملف يدوياً.

### ج. إزالة القيم الثابتة (Hardcoded Values)
لجعل التحليل اليدوي مرناً، يجب أن يسأل البوت المستخدم عن العملة التي يريد تحليلها.

**تعديل مقترح لـ `src/bot_interface/handlers.py`:**
1.  **تغيير قائمة التحليل:**
    عندما يضغط المستخدم على "📊 تحليل موجي"، بدلاً من عرض الأطر الزمنية، اعرض قائمة بأشهر العملات من `config.yaml` مع زر "أخرى".
    ```python
    # Inside wave_analysis_menu function
    top_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"] # Or get from config
    keyboard = []
    for symbol in top_symbols:
        # The callback_data now includes the action and the symbol
        keyboard.append([InlineKeyboardButton(symbol, callback_data=f'select_symbol_{symbol}')])

    keyboard.append([InlineKeyboardButton("عملة أخرى...", callback_data='select_symbol_other')])
    keyboard.append([InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')])

    # Ask the user to select a symbol
    text = "اختر العملة للتحليل:"
    # ... send message with this keyboard
    ```
2.  **حفظ اختيار المستخدم:**
    عندما يضغط المستخدم على عملة، احفظها في `context.user_data`.
    ```python
    # Inside the button handler
    if data.startswith('select_symbol_'):
        symbol = data.split('_')[2]
        context.user_data['selected_symbol'] = symbol
        # Now, show the timeframe menu
        await show_timeframe_menu(update, context) # A new function to show timeframes
    ```
3.  **استخدام القيمة المحفوظة:**
    في دالة `_handle_strategy_analysis`، اقرأ العملة من `context.user_data` بدلاً من `BTCUSDT`.
    ```python
    # Inside _handle_strategy_analysis
    symbol = context.user_data.get('selected_symbol', 'BTCUSDT') # Default to BTC for safety
    patterns = await asyncio.to_thread(strategy_func, symbol)
    # ... rest of the function
    ```

---

## 5. مراجعة الاختبارات الحالية (Testing Review)

تم إنشاء بنية تحتية للاختبارات في مجلد `tests/`، وهذا أمر جيد. لكن عند فحص الملفات، تبين أن **جميع ملفات الاختبارات هي مجرد قوالب فارغة**.

- `tests/test_bot_interface.py`: فارغ.
- `tests/test_data_fetching.py`: فارغ.
- `tests/test_elliott_wave_engine.py`: فارغ.

### تقييم الوضع الحالي
- **الوضع:** 🔴 **حرج وخطير**.
- **المشكلة:** لا توجد أي اختبارات آلية (Automated Tests) للمشروع. هذا يعني أنه لا توجد أي طريقة للتأكد من أن:
    - **محرك موجات إليوت** يعمل بشكل صحيح ويحدد الأنماط بدقة.
    - **جلب البيانات** من Bybit يتم بشكل سليم.
    - **الاستراتيجيات** تتخذ القرارات الصحيحة.
    - أي **تعديل جديد** على الكود لا يتسبب في كسر الميزات القديمة (Regression).

### التوصية
- **الأولوية القصوى:** يجب البدء **فوراً** في كتابة اختبارات الوحدات (Unit Tests)، خاصة لمجلد `src/elliott_wave_engine` لأنه الجزء الأكثر تعقيداً وحساسية في المشروع.
- **مثال للاختبار:**
    - قم بإنشاء بيانات سعرية وهمية (mock data) تمثل نمط موجة دافعة (Impulse Wave) مثالي.
    - مرر هذه البيانات إلى محرك موجات إليوت.
    - تأكد من أن المحرك يتعرف على هذا النمط بشكل صحيح.
    - كرر العملية لأنماط أخرى (Zigzag, Flat, etc.) وحالات فشل متوقعة.
- **الفائدة:** كتابة الاختبارات هي الطريقة الوحيدة لضمان موثوقية البوت وتقليل المخاطر بشكل كبير عند تشغيله بأموال حقيقية.
