#!/bin/bash

echo "🚀 KEEPING SYSTEM AWAKE FOR BIRDY OPERATIONS"
echo "============================================="

# Start caffeinate to prevent all types of sleep
caffeinate -d -i -m -s -u -t 86400 &
CAFFEINE_PID=$!

echo "✅ Started background caffeinate (PID: $CAFFEINE_PID)"
echo "   • Prevents display sleep (-d)"
echo "   • Prevents idle sleep (-i)" 
echo "   • Prevents disk sleep (-m)"
echo "   • Prevents system sleep (-s)"
echo "   • Prevents user idle sleep (-u)"
echo "   • Running for 24 hours (-t 86400)"

# Create LaunchAgent for permanent solution
PLIST_PATH="$HOME/Library/LaunchAgents/com.forturro.birdy.keepawake.plist"

cat > "$PLIST_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.forturro.birdy.keepawake</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/caffeinate</string>
        <string>-d</string>
        <string>-i</string>
        <string>-m</string>
        <string>-s</string>
        <string>-u</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load the launch agent
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo "✅ Created permanent LaunchAgent"
echo "   • Will automatically start on boot"
echo "   • Keeps system awake 24/7"

echo ""
echo "🔧 MANUAL SETTINGS TO COMPLETE:"
echo "   1. Open System Settings → Lock Screen"
echo "   2. Set 'Start Screen Saver when inactive' to Never"
echo "   3. Set 'Turn display off when inactive' to Never (both battery and power)"
echo "   4. Turn OFF 'Require password after screen saver begins'"
echo ""
echo "✅ BIRDY IS NOW CONFIGURED FOR 24/7 OPERATION!"
echo "   Your system will stay awake for continuous automation."

# Save PID for easy stopping
echo $CAFFEINE_PID > /tmp/birdy_caffeinate.pid
echo ""
echo "💡 To stop: kill \$(cat /tmp/birdy_caffeinate.pid)"
echo "💡 To restart: ./keep_awake_simple.sh"