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
