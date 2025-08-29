#!/bin/bash

# auto_restart_bot.sh - تشغيل البوت مع إعادة التشغيل التلقائي عند التغيير

# متغيرات التكوين
BOT_DIR="/root/THE-BEST-BOT"
BOT_SCRIPT="bot.py"  # تم التعديل إلى اسم الملف الصحيح
LOG_FILE="bot_auto_restart.log"
PID_FILE="bot.pid"
WATCH_DIRS="src config"  # المجلدات المراد مراقبتها

# الانتقال إلى مجلد البوت
cd "$BOT_DIR" || exit 1

# دالة لتسجيل الرسائل مع الوقت
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# دالة لإيقاف البوت
stop_bot() {
    if [ -f "$PID_FILE" ]; then
        BOT_PID=$(cat "$PID_FILE")
        if ps -p "$BOT_PID" > /dev/null 2>&1; then
            log_message "إيقاف البوت (PID: $BOT_PID)..."
            kill -TERM "$BOT_PID"
            sleep 3
            if ps -p "$BOT_PID" > /dev/null 2>&1; then
                log_message "إجبار إيقاف البوت..."
                kill -KILL "$BOT_PID"
            fi
        fi
        rm -f "$PID_FILE"
    fi

    # إيقاف أي عمليات python متعلقة بالبوت
    pkill -f "$BOT_SCRIPT" 2>/dev/null || true
    sleep 2
}

# دالة لبدء البوت
start_bot() {
    log_message "بدء تشغيل البوت..."

    # التحقق من وجود الملف الرئيسي
    if [ ! -f "$BOT_SCRIPT" ]; then
        log_message "خطأ: لم يتم العثور على $BOT_SCRIPT"
        exit 1
    fi

    # بدء البوت في الخلفية
    python3 "$BOT_SCRIPT" > bot_output.log 2>&1 &
    BOT_PID=$!
    echo $BOT_PID > "$PID_FILE"

    # التحقق من نجاح التشغيل
    sleep 3
    if ps -p "$BOT_PID" > /dev/null 2>&1; then
        log_message "تم تشغيل البوت بنجاح (PID: $BOT_PID)"
    else
        log_message "فشل في تشغيل البوت"
        rm -f "$PID_FILE"
        return 1
    fi
}

# دالة لإعادة تشغيل البوت
restart_bot() {
    log_message "إعادة تشغيل البوت بسبب تغيير في الملفات..."
    stop_bot
    sleep 2
    start_bot
}

# دالة للتنظيف عند الإنهاء
cleanup() {
    log_message "إيقاف مراقب الملفات..."
    stop_bot
    exit 0
}

# تعيين معالج الإشارات
trap cleanup SIGINT SIGTERM

# التحقق من وجود inotify-tools
if ! command -v inotifywait &> /dev/null; then
    log_message "تثبيت inotify-tools..."
    apt-get update && apt-get install -y inotify-tools
fi

log_message "بدء مراقب البوت التلقائي..."
log_message "مراقبة المجلدات: $WATCH_DIRS"

# بدء البوت أول مرة
start_bot

# مراقبة التغييرات في الملفات
while true; do
    # مراقبة التغييرات في المجلدات المحددة
    if inotifywait -r -e modify,create,delete,move $WATCH_DIRS 2>/dev/null; then
        log_message "تم اكتشاف تغيير في الملفات"
        restart_bot
        sleep 5  # انتظار قصير لتجنب إعادة التشغيل المتكررة
    fi

    # التحقق من حالة البوت كل دقيقة
    if [ -f "$PID_FILE" ]; then
        BOT_PID=$(cat "$PID_FILE")
        if ! ps -p "$BOT_PID" > /dev/null 2>&1; then
            log_message "البوت متوقف بشكل غير متوقع، إعادة تشغيل..."
            start_bot
        fi
    else
        log_message "ملف PID مفقود، إعادة تشغيل البوت..."
        start_bot
    fi

    sleep 10
done
