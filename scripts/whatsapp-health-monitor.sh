#!/bin/bash

# WhatsApp Health Monitor - Telegram Alert Version
# Monitors connection health and sends Telegram alerts to Jeff (no auto-restarts)

LOG_FILE="/tmp/whatsapp-health.log"
STATE_FILE="/tmp/whatsapp-health-state.json"
FLAP_THRESHOLD=3
ALERT_COOLDOWN=1800  # 30 minutes between alerts

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_connection_health() {
    # Get WhatsApp status from OpenClaw
    local gateway_status=$(openclaw status 2>/dev/null)
    local whatsapp_status=$(echo "$gateway_status" | grep -i "whatsapp" | head -1)
    
    # Count recent connection issues (last 10 minutes) 
    local recent_disconnects=$(openclaw logs 2>/dev/null | tail -100 | grep -c "WhatsApp.*disconnected" 2>/dev/null || echo "0")
    local recent_499_errors=$(openclaw logs 2>/dev/null | tail -100 | grep -c "status.*499" 2>/dev/null || echo "0")
    local credential_corruption=$(openclaw logs 2>/dev/null | tail -100 | grep -c "corrupted.*WhatsApp" 2>/dev/null || echo "0")
    
    # Clean up any newlines and ensure numeric values
    recent_disconnects=$(echo "$recent_disconnects" | tr -d '\n' | grep -o '[0-9]*' | head -1)
    recent_499_errors=$(echo "$recent_499_errors" | tr -d '\n' | grep -o '[0-9]*' | head -1)
    credential_corruption=$(echo "$credential_corruption" | tr -d '\n' | grep -o '[0-9]*' | head -1)
    
    # Default to 0 if empty
    recent_disconnects=${recent_disconnects:-0}
    recent_499_errors=${recent_499_errors:-0}
    credential_corruption=${credential_corruption:-0}
    
    log "Health check - Disconnects: $recent_disconnects, 499 errors: $recent_499_errors, Corruption: $credential_corruption"
    
    # Determine overall health
    local total_issues=$((recent_disconnects + recent_499_errors + credential_corruption))
    
    # Check if WhatsApp shows as connected/linked
    local is_connected=0
    if echo "$whatsapp_status" | grep -E "(OK|LINKED|connected)" > /dev/null 2>&1; then
        is_connected=1
    fi
    
    # Update state file
    cat > "$STATE_FILE" << EOF
{
    "last_check": "$(date -Iseconds)",
    "is_connected": $is_connected,
    "recent_issues": $total_issues,
    "disconnects": $recent_disconnects,
    "status_499": $recent_499_errors,
    "corruption": $credential_corruption,
    "whatsapp_status": "$whatsapp_status",
    "health_score": $((100 - (total_issues * 10)))
}
EOF
    
    # Return health assessment
    if [[ $is_connected -eq 1 ]] && [[ $total_issues -lt $FLAP_THRESHOLD ]]; then
        return 0  # Healthy
    else
        return 1  # Unhealthy
    fi
}

should_send_alert() {
    # Check if we've alerted recently (cooldown period)
    local last_alert_file="/tmp/whatsapp-last-alert"
    local now=$(date +%s)
    
    if [[ -f "$last_alert_file" ]]; then
        local last_alert=$(cat "$last_alert_file")
        local time_since_alert=$((now - last_alert))
        
        if [[ $time_since_alert -lt $ALERT_COOLDOWN ]]; then
            log "⏳ Alert cooldown active ($(((ALERT_COOLDOWN - time_since_alert) / 60)) minutes remaining)"
            return 1
        fi
    fi
    
    return 0
}

send_health_alert() {
    if ! should_send_alert; then
        return 1
    fi
    
    local state_content=$(cat "$STATE_FILE" 2>/dev/null || echo "{}")
    local health_score=$(echo "$state_content" | grep -o '"health_score": [0-9]*' | grep -o '[0-9]*' || echo "0")
    local recent_issues=$(echo "$state_content" | grep -o '"recent_issues": [0-9]*' | grep -o '[0-9]*' || echo "0")
    
    # Craft alert message
    local alert_msg="🟡 WhatsApp Health Alert
    
Health Score: ${health_score}/100
Recent Issues: ${recent_issues} (last 10 min)

Recommended Actions:
• Check WhatsApp connection status
• Consider gateway restart if issues persist
• Monitor for 15 minutes before manual intervention

Status Details:
$(cat "$STATE_FILE" 2>/dev/null | tr ',' '\n' | sed 's/[{}"]//g' | grep -E "(connected|issues|status)" | head -5)"

    # Send alert to WhatsApp group
    # Send alert to Jeff's Telegram DM (NOT WhatsApp Forturro Group)
    local alert_msg="🟡 WhatsApp Health Alert
    
Health Score: ${health_score}/100
Recent Issues: ${recent_issues} (last 10 min)

Recommended Actions:
• Check WhatsApp connection status
• Consider gateway restart if issues persist
• Monitor for 15 minutes before manual intervention"

    # Send alert to Jeff's Telegram DM (ID: 8685619460)
    echo "$alert_msg" | openclaw message send --channel telegram --target "8685619460" 2>&1 | tee -a "$LOG_FILE"
    
    # Record alert time
    date +%s > "/tmp/whatsapp-last-alert"
    log "📢 Health alert sent to Jeff's Telegram DM"
}

check_and_report() {
    log "🔍 Checking WhatsApp health (non-intrusive)..."
    
    if check_connection_health; then
        log "✅ WhatsApp connection healthy"
        # Clear any previous alert state on recovery
        rm -f "/tmp/whatsapp-last-alert" 2>/dev/null
    else
        log "⚠️ WhatsApp health issues detected"
        send_health_alert
    fi
}

# Show current health status if --status flag
if [[ "$1" == "--status" ]]; then
    if [[ -f "$STATE_FILE" ]]; then
        echo "📊 WhatsApp Health Status:"
        cat "$STATE_FILE" | jq . 2>/dev/null || cat "$STATE_FILE"
    else
        echo "No health data available yet"
    fi
    exit 0
fi

# Run health check
check_and_report