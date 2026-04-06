#!/bin/bash
# Lead Alert Monitor — Dave Ramsey & HomeLight
# Runs via system cron. Zero LLM tokens. Checks Gmail, alerts WhatsApp group.

set -euo pipefail

STATE_FILE="/Users/claw1/.openclaw/workspace/memory/lead-alerts-state.json"
LOG_FILE="/Users/claw1/.openclaw/workspace/memory/lead-alerts.log"
WHATSAPP_GROUP="120363029651955145@g.us"
GOG="/opt/homebrew/bin/gog"
OPENCLAW="/opt/homebrew/bin/openclaw"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

# Ensure state file exists
if [ ! -f "$STATE_FILE" ]; then
  echo '{"last_seen_message_ids":[],"last_checked":"","last_alert_sent":""}' > "$STATE_FILE"
fi

# Search Gmail for lead emails (newer_than:2d keeps results fresh, state file prevents dupes)
RESULTS=$($GOG gmail messages search '((from:followupboss subject:"DaveRamsey") OR (from:"homelight referrals" OR subject:"new referral from homelight")) newer_than:2d' --max 20 --json --account jeff@forturro.com 2>/dev/null) || {
  log "ERROR: gog gmail search failed"
  exit 1
}

# Get count of results
MSG_COUNT=$(echo "$RESULTS" | jq -r '.messages | length' 2>/dev/null || echo "0")
if [ "$MSG_COUNT" = "0" ] || [ "$MSG_COUNT" = "null" ]; then
  log "No emails found in search"
  # Update last_checked
  jq --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" '.last_checked = $ts' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  exit 0
fi

# Get known IDs
KNOWN_IDS=$(jq -r '.last_seen_message_ids[]' "$STATE_FILE" 2>/dev/null || true)

# Find new messages
NEW_COUNT=0
while IFS= read -r line; do
  ID=$(echo "$line" | jq -r '.id')
  SUBJECT=$(echo "$line" | jq -r '.subject // ""')
  FROM=$(echo "$line" | jq -r '.from // ""')
  
  # Skip if already known
  if echo "$KNOWN_IDS" | grep -qF "$ID" 2>/dev/null; then
    continue
  fi
  
  # Determine lead type and send alert
  if echo "$SUBJECT" | grep -qi "daveramsey\|dave ramsey"; then
    # Extract lead name from subject (format: "New Lead from DaveRamsey - Name")
    LEAD_NAME=$(echo "$SUBJECT" | sed 's/.*DaveRamsey - //' | sed 's/.*Dave Ramsey - //')
    MSG="🚨 DAVE RAMSEY LEAD 🚨
$LEAD_NAME
Check FUB for details."
    $OPENCLAW message send --channel whatsapp --target "$WHATSAPP_GROUP" --message "$MSG" 2>/dev/null && {
      log "ALERT SENT: Dave Ramsey — $LEAD_NAME (id: $ID)"
    } || {
      log "ERROR: Failed to send Dave Ramsey alert for $ID"
    }
    NEW_COUNT=$((NEW_COUNT + 1))
  elif echo "$FROM" | grep -qi "homelight"; then
    # Extract details from subject
    LEAD_INFO="$SUBJECT"
    MSG="🚨 HOMELIGHT LEAD 🚨
$LEAD_INFO
Check FUB for details."
    $OPENCLAW message send --channel whatsapp --target "$WHATSAPP_GROUP" --message "$MSG" 2>/dev/null && {
      log "ALERT SENT: HomeLight — $LEAD_INFO (id: $ID)"
    } || {
      log "ERROR: Failed to send HomeLight alert for $ID"
    }
    NEW_COUNT=$((NEW_COUNT + 1))
  fi
  
  # Add to known IDs immediately (even if send fails, to prevent spam retries)
  KNOWN_IDS="$KNOWN_IDS
$ID"
  
done < <(echo "$RESULTS" | jq -c '.messages[]')

# Update state file with all current message IDs
ALL_IDS=$(echo "$RESULTS" | jq '[.messages[].id]')
MERGED=$(jq --argjson new "$ALL_IDS" '[.last_seen_message_ids[], ($new[])] | unique' "$STATE_FILE")
NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

if [ "$NEW_COUNT" -gt 0 ]; then
  jq --argjson ids "$MERGED" --arg ts "$NOW" --arg alert "$NOW" \
    '.last_seen_message_ids = $ids | .last_checked = $ts | .last_alert_sent = $alert' \
    "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  log "Found $NEW_COUNT new lead(s)"
else
  jq --argjson ids "$MERGED" --arg ts "$NOW" \
    '.last_seen_message_ids = $ids | .last_checked = $ts' \
    "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
fi
