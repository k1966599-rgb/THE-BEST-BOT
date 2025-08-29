#!/bin/bash

# Ensure the script is run from its own directory
cd "$(dirname "$0")"

# --- Configuration ---
LOCK_FILE="/tmp/bot.lock"
LOG_FILE="bot.log"

# --- Cleanup function ---
cleanup() {
    echo "Caught signal, cleaning up lock file..."
    rm -f "$LOCK_FILE"
    exit 0
}

# --- Trap signals for cleanup ---
trap cleanup SIGINT SIGTERM

# --- Main Logic ---

# 1. Check for a lock file to prevent multiple instances
if [ -e "$LOCK_FILE" ]; then
    # Check if the process holding the lock is still running
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null; then
        echo "Bot is already running with PID $PID. Exiting."
        exit 1
    else
        echo "Found stale lock file. Removing it."
        rm -f "$LOCK_FILE"
    fi
fi

# 2. Create a new lock file with the current script's PID
echo $$ > "$LOCK_FILE"

echo "Starting bot daemon..."

# 3. Infinite loop to manage the bot process
while true; do
    # Check for git updates (optional, can be commented out)
    git fetch origin main > /dev/null 2>&1
    if [ $(git rev-parse HEAD) != $(git rev-parse origin/main) ]; then
        echo "Update found. Pulling changes..."
        git pull origin main
        echo "Installing/updating dependencies..."
        pip install -r requirements.txt
    fi

    # 4. Start the bot if it's not running
    if ! pgrep -f "python3 bot.py" > /dev/null; then
        echo "Bot process not found. Starting bot..."
        # Touch the log file to ensure it exists
        touch "$LOG_FILE"
        # Run the bot in the background, appending to the log
        nohup python3 bot.py >> "$LOG_FILE" 2>&1 &
    fi

    # 5. Wait before checking again
    sleep 60
done
