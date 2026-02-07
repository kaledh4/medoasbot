#!/bin/bash

# Cron job test script for Telegram bot and dashboard
# This script will be executed periodically to test the workflow

echo "🚀 Starting cron job test at $(date)"

# Set environment variables for Telegram (you'll need to set these in your actual environment)
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# Run Telegram bot test
if python3 /root/.openclaw/workspace/propaganda-pipeline/tests/telegram-bot/test_bot.py; then
    echo "✅ Telegram bot test completed successfully"
    TELEGRAM_STATUS="success"
else
    echo "❌ Telegram bot test failed"
    TELEGRAM_STATUS="failed"
fi

# Run dashboard test
if python3 /root/.openclaw/workspace/propaganda-pipeline/tests/dashboard/test_dashboard.py; then
    echo "✅ Dashboard test completed successfully"
    DASHBOARD_STATUS="success"
else
    echo "❌ Dashboard test failed"
    DASHBOARD_STATUS="failed"
fi

# Send Telegram notification with test results
MESSAGE="📊 Cron Job Test Results\n\n"
MESSAGE+="📩 Telegram Bot: ${TELEGRAM_STATUS}\n"
MESSAGE+="📊 Dashboard: ${DASHBOARD_STATUS}\n\n"
MESSAGE+="📅 Time: $(date)"

curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\": \"$TELEGRAM_CHAT_ID\", \"text\": \"$MESSAGE\", \"parse_mode\": \"HTML\"}" > /dev/null

echo "✨ Cron job test completed at $(date)"
echo "----------------------------------------"