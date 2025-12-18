#!/bin/bash
# Auto-restart script for CV Analysis Bot
# Runs 24/7 with automatic restart on failure

cd /home/ubuntu/telegram_ai_bot

while true; do
    echo "$(date): Starting bot..."
    python3 bot.py
    echo "$(date): Bot stopped. Restarting in 5 seconds..."
    sleep 5
done
