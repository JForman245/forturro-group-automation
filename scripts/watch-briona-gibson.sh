#!/bin/bash
# Watch for Briona Gibson contract signature on Homewood Rd
# Checks Gmail + Dotloop notifications for signing activity

set -euo pipefail

STATE_FILE="/Users/claw1/.openclaw/workspace/memory/watch-briona-gibson.json"
LOG_FILE="/Users/claw1/.openclaw/workspace/memory/lead-alerts.log"
GOG="/opt/homebrew/bin/gog"
OPENCLAW="/opt/homebrew/bin/openclaw"
TARGET_CHAT="+18439024325"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] BRIONA-WATCH: $*" >> "$LOG_FILE"; }

# Ensure state file exists
if [ ! -f "$STATE_FILE" ]; then
  echo '{"alerted":false,"seen_ids":[],"created":"2026-04-05T13:14:00Z"}' > "$STATE_FILE"
fi

# Already alerted? Skip.
ALERTED=$(jq -r '.alerted' "$STATE_FILE")
if [ "$ALERTED" = "true" ]; then
  exit 0
fi

# Search Gmail for signing-related emails mentioning Briona Gibson or Homewood
RESULTS=$($GOG gmail messages search '(briona gibson homewood) OR (briona gibson signed) OR (briona gibson contract) OR (homewood subject:signed) OR (homewood subject:completed)' --max 10 --json --account jeff@forturro.com 2>/dev/null) || {
  log "ERROR: Gmail search failed"
  exit 1
}

MSG_COUNT=$(echo "$RESULTS" | jq -r '.messages | length' 2>/dev/null || echo "0")
if [ "$MSG_COUNT" = "0" ] || [ "$MSG_COUNT" = "null" ]; then
  jq --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" '.last_checked = $ts' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  exit 0
fi

SEEN_IDS=$(jq -r '.seen_ids[]' "$STATE_FILE" 2>/dev/null || true)

while IFS= read -r line; do
  ID=$(echo "$line" | jq -r '.id')
  SUBJECT=$(echo "$line" | jq -r '.subject // ""')
  FROM=$(echo "$line" | jq -r '.from // ""')
  DATE=$(echo "$line" | jq -r '.date // ""')

  # Skip already seen
  if echo "$SEEN_IDS" | grep -qF "$ID" 2>/dev/null; then
    continue
  fi

  # Check if this looks like a signing notification
  SUBJECT_LOWER=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
  if echo "$SUBJECT_LOWER" | grep -qE "sign|complete|executed|counter"; then
    MSG="📝 Briona Gibson — looks like a contract activity on Homewood Rd:
$SUBJECT
From: $FROM ($DATE)"
    $OPENCLAW message send --channel whatsapp --target "$TARGET_CHAT" --message "$MSG" 2>/dev/null && {
      log "ALERT SENT: Briona Gibson signing — $SUBJECT"
      jq '.alerted = true' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    } || {
      log "ERROR: Failed to send alert"
    }
    break
  fi
  
  SEEN_IDS="$SEEN_IDS
$ID"
done < <(echo "$RESULTS" | jq -c '.messages[]')

# Update state
ALL_IDS=$(echo "$RESULTS" | jq '[.messages[].id]')
MERGED=$(jq --argjson new "$ALL_IDS" '[.seen_ids[], ($new[])] | unique' "$STATE_FILE")
jq --argjson ids "$MERGED" --arg ts "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" '.seen_ids = $ids | .last_checked = $ts' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
