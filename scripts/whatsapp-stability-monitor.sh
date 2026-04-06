#!/bin/bash

# WhatsApp Connection Stability Monitor
# Auto-fixes flapping connections when 499 errors or credential corruption detected

LOG_FILE="/tmp/whatsapp-stability.log"
FLAP_THRESHOLD=3  # Number of disconnections in check period to trigger fix
CHECK_PERIOD="5m" # How far back to look for flapping

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_connection_flapping() {
    # Get recent logs and count WhatsApp connection issues
    local recent_issues=$(openclaw logs 2>/dev/null | grep -E "(WhatsApp.*disconnected|status.*499|corrupted.*WhatsApp|web reconnect)" | tail -20 | wc -l)
    
    # Check for credential corruption specifically
    local corruption_detected=$(openclaw logs 2>/dev/null | grep -c "restored corrupted WhatsApp creds.json" | tail -5)
    
    log "Recent connection issues: $recent_issues, Corruption events: $corruption_detected"
    
    # If we see flapping or corruption, trigger fix
    if [[ $recent_issues -ge $FLAP_THRESHOLD ]] || [[ $corruption_detected -gt 0 ]]; then
        return 0  # Flapping detected
    else
        return 1  # Connection stable
    fi
}

fix_whatsapp_connection() {
    log "🔧 WhatsApp connection flapping detected - applying automatic fix"
    
    # Method 1: Clean gateway restart (most effective)
    log "Restarting OpenClaw gateway to clear corrupted state..."
    openclaw gateway restart 2>&1 | tee -a "$LOG_FILE"
    
    # Wait for restart to complete
    sleep 10
    
    # Verify fix worked
    local status=$(openclaw status 2>/dev/null | grep "WhatsApp" | grep -o "OK\|LINKED")
    if [[ "$status" == "OK" ]] || [[ "$status" == "LINKED" ]]; then
        log "✅ WhatsApp connection restored successfully"
        return 0
    else
        log "⚠️ Gateway restart didn't resolve issue - trying credential cleanup"
        
        # Method 2: Clean credential files if restart didn't work
        local creds_path="/Users/claw1/.openclaw/credentials/whatsapp/default/creds.json"
        if [[ -f "$creds_path" ]]; then
            log "Backing up and cleaning WhatsApp credentials..."
            cp "$creds_path" "${creds_path}.backup.$(date +%s)" 2>/dev/null
            rm -f "$creds_path" 2>/dev/null
            openclaw gateway restart 2>&1 | tee -a "$LOG_FILE"
            sleep 10
        fi
        
        log "🔄 Manual re-authentication may be required"
        return 1
    fi
}

main() {
    log "🔍 Checking WhatsApp connection stability..."
    
    if check_connection_flapping; then
        fix_whatsapp_connection
    else
        log "✅ WhatsApp connection stable"
    fi
}

# Run the check
main