#!/usr/bin/env python3
"""
Keep Mac awake for continuous Birdy operations
Prevents sleep, screen lock, and display dimming
"""

import subprocess
import os
import time
from datetime import datetime

def disable_sleep_settings():
    """Configure system to never sleep"""
    print("🔧 Configuring system sleep settings...")
    
    commands = [
        # Disable sleep on AC power
        ["sudo", "pmset", "-c", "sleep", "0"],
        ["sudo", "pmset", "-c", "displaysleep", "0"], 
        ["sudo", "pmset", "-c", "disksleep", "0"],
        
        # Disable sleep on battery (optional)
        ["sudo", "pmset", "-b", "sleep", "30"],  # 30 min on battery
        ["sudo", "pmset", "-b", "displaysleep", "10"],  # 10 min display on battery
        
        # Disable hibernation
        ["sudo", "pmset", "-a", "hibernatemode", "0"],
        
        # Disable sudden motion sensor sleep
        ["sudo", "pmset", "-a", "sms", "0"],
    ]
    
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ {' '.join(cmd[2:])}")
            else:
                print(f"  ❌ Failed: {' '.join(cmd[2:])}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def create_caffeinate_service():
    """Create a background service to keep system awake"""
    service_content = """#!/bin/bash
# Keep system awake for Birdy operations
while true; do
    caffeinate -d -i -m -s -u &
    CAFFEINE_PID=$!
    sleep 3600  # Run for 1 hour
    kill $CAFFEINE_PID 2>/dev/null
done
"""
    
    script_path = "/Users/claw1/.openclaw/workspace/caffeinate_daemon.sh"
    with open(script_path, 'w') as f:
        f.write(service_content)
    
    os.chmod(script_path, 0o755)
    print(f"✅ Created caffeinate daemon: {script_path}")

def start_background_caffeinate():
    """Start caffeinate in background to prevent sleep"""
    try:
        # Start caffeinate with all flags to prevent any type of sleep
        process = subprocess.Popen([
            'caffeinate', 
            '-d',  # Prevent display from sleeping
            '-i',  # Prevent system from idle sleeping  
            '-m',  # Prevent disk from sleeping
            '-s',  # Prevent system from sleeping
            '-u',  # Prevent user idle system sleep
            '-t', '86400'  # Run for 24 hours
        ])
        
        print(f"✅ Started background caffeinate (PID: {process.pid})")
        print("  System will stay awake for 24 hours")
        return process.pid
        
    except Exception as e:
        print(f"❌ Error starting caffeinate: {e}")
        return None

def check_current_settings():
    """Check current power management settings"""
    print("🔍 Current power management settings:")
    
    try:
        result = subprocess.run(['pmset', '-g'], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error checking settings: {e}")

def create_launch_agent():
    """Create a LaunchAgent to keep system awake on startup"""
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
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
</plist>"""

    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.forturro.birdy.keepawake.plist")
    
    try:
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        # Load the launch agent
        subprocess.run(['launchctl', 'load', plist_path])
        print(f"✅ Created and loaded LaunchAgent: {plist_path}")
        print("  System will automatically stay awake on startup")
        
    except Exception as e:
        print(f"❌ Error creating LaunchAgent: {e}")

def main():
    print("🚀 CONFIGURING SYSTEM TO STAY AWAKE FOR BIRDY")
    print("=" * 60)
    
    print("\n1. Checking current settings...")
    check_current_settings()
    
    print("\n2. Starting immediate background caffeinate...")
    pid = start_background_caffeinate()
    
    print("\n3. Creating permanent LaunchAgent...")
    create_launch_agent()
    
    print("\n4. Manual system settings needed:")
    print("  Go to: System Settings → Lock Screen")
    print("  • Set screen saver to 'Never'")
    print("  • Set display sleep to 'Never' on power adapter")
    print("  • Turn OFF password requirement")
    
    print(f"\n✅ SYSTEM CONFIGURED FOR 24/7 BIRDY OPERATIONS")
    print("  • Background caffeinate running")
    print("  • LaunchAgent will restart on boot")
    print("  • Birdy can now work around the clock!")
    
    if pid:
        print(f"\n💡 To manually stop: kill {pid}")
        print(f"💡 To restart: python3 keep_system_awake.py")

if __name__ == "__main__":
    main()