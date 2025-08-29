#!/bin/bash

# bot_manager.sh - إدارة البوت (تشغيل، إيقاف، حالة)

BOT_DIR="/root/THE-BEST-BOT"
AUTO_SCRIPT="auto_restart_bot.sh"
AUTO_PID_FILE="auto_bot.pid"

cd "$BOT_DIR" || exit 1

case "$1" in
    start)
        if [ -f "$AUTO_PID_FILE" ]; then
            AUTO_PID=$(cat "$AUTO_PID_FILE")
            if ps -p "$AUTO_PID" > /dev/null 2>&1; then
                echo "البوت يعمل بالفعل (PID: $AUTO_PID)"
                exit 1
            fi
        fi

        echo "بدء تشغيل البوت..."
        nohup ./"$AUTO_SCRIPT" > auto_bot_daemon.log 2>&1 &
        AUTO_PID=$!
        echo $AUTO_PID > "$AUTO_PID_FILE"
        echo "تم بدء تشغيل البوت في الخلفية (PID: $AUTO_PID)"
        echo "لمتابعة السجلات: tail -f bot_auto_restart.log"
        ;;

    stop)
        if [ -f "$AUTO_PID_FILE" ]; then
            AUTO_PID=$(cat "$AUTO_PID_FILE")
            if ps -p "$AUTO_PID" > /dev/null 2>&1; then
                echo "إيقاف البوت..."
                kill -TERM "$AUTO_PID"
                sleep 3
                if ps -p "$AUTO_PID" > /dev/null 2>&1; then
                    kill -KILL "$AUTO_PID"
                fi
                rm -f "$AUTO_PID_FILE"

                # إيقاف البوت الفرعي أيضاً
                if [ -f "bot.pid" ]; then
                    BOT_PID=$(cat "bot.pid")
                    kill -TERM "$BOT_PID" 2>/dev/null || true
                    rm -f "bot.pid"
                fi

                echo "تم إيقاف البوت"
            else
                echo "البوت غير قيد التشغيل"
                rm -f "$AUTO_PID_FILE"
            fi
        else
            echo "البوت غير قيد التشغيل"
        fi
        ;;

    restart)
        $0 stop
        sleep 3
        $0 start
        ;;

    status)
        if [ -f "$AUTO_PID_FILE" ]; then
            AUTO_PID=$(cat "$AUTO_PID_FILE")
            if ps -p "$AUTO_PID" > /dev/null 2>&1; then
                echo "✅ مراقب البوت يعمل (PID: $AUTO_PID)"

                if [ -f "bot.pid" ]; then
                    BOT_PID=$(cat "bot.pid")
                    if ps -p "$BOT_PID" > /dev/null 2>&1; then
                        echo "✅ البوت يعمل (PID: $BOT_PID)"
                    else
                        echo "❌ البوت متوقف"
                    fi
                else
                    echo "❌ البوت غير قيد التشغيل"
                fi
            else
                echo "❌ مراقب البوت متوقف"
                rm -f "$AUTO_PID_FILE"
            fi
        else
            echo "❌ البوت غير قيد التشغيل"
        fi
        ;;

    logs)
        if [ -f "bot_auto_restart.log" ]; then
            tail -f bot_auto_restart.log
        else
            echo "لا توجد ملفات سجلات"
        fi
        ;;

    clean)
        echo "تنظيف ملفات السجلات القديمة..."
        find . -name "*.log" -mtime +7 -delete
        echo "تم حذف السجلات الأقدم من 7 أيام"
        ;;

    *)
        echo "الاستخدام: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "الأوامر:"
        echo "  start   - تشغيل البوت"
        echo "  stop    - إيقاف البوت"
        echo "  restart - إعادة تشغيل البوت"
        echo "  status  - عرض حالة البوت"
        echo "  logs    - متابعة سجلات البوت"
        echo "  clean   - تنظيف السجلات القديمة"
        exit 1
        ;;
esac
