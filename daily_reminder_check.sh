#!/bin/bash

# Daily 7 AM Apple Reminders check
# This script will send you a WhatsApp message about your reminders

# Get today's reminders
reminders=$(remindctl today --json 2>/dev/null)

if [ $? -eq 0 ] && [ "$reminders" != "[]" ]; then
    count=$(echo "$reminders" | jq length)
    message="📅 Good morning Jeff! You have $count reminders due today. Check your Reminders app. 🐦"
else
    message="📅 Good morning Jeff! No reminders due today. Have a great day! 🐦"
fi

# Send WhatsApp message (when the CLI pairing works)
# openclaw message send --channel whatsapp --target +18439024325 --message "$message"

# For now, just log it
echo "$(date): $message" >> /Users/claw1/.openclaw/workspace/daily_reminders.log

echo "$message"