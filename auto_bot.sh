#!/bin/bash
cd /root/bot-telegram
while true; do
    git fetch origin main 2>/dev/null
    if [ $(git rev-parse HEAD) != $(git rev-parse origin/main) ]; then
        echo "[$(date)] تحديث متوفر، جاري السحب..."
        git pull origin main
        pkill -f "python3 bot.py" 2>/dev/null
        sleep 2
        nohup python3 bot.py > bot.log 2>&1 &
        echo "[$(date)] البوت تم إعادة تشغيله مع آخر تحديث"
    fi
    if ! pgrep -f "python3 bot.py" > /dev/null; then
        echo "[$(date)] البوت متوقف، جاري إعادة التشغيل..."
        nohup python3 bot.py > bot.log 2>&1 &
    fi
    sleep 10
done
