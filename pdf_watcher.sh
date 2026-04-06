#!/bin/bash
# Watches the Drop folder and processes any new PDFs
DROPFOLDER="$HOME/Desktop/Drop PDFs for Birdy"
INBOX="$HOME/.openclaw/workspace/pdf_inbox"
PROCESSED="$DROPFOLDER/.processed"
mkdir -p "$INBOX" "$PROCESSED"

for f in "$DROPFOLDER"/*.pdf "$DROPFOLDER"/*.PDF; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f")
    
    # Skip if already processed
    [ -f "$PROCESSED/$BASENAME" ] && continue
    
    # Process it
    cp "$f" "$INBOX/"
    /usr/bin/python3 "$HOME/.openclaw/workspace/pdf_reader.py" "$INBOX/$BASENAME" 2>&1
    
    # Mark as processed
    touch "$PROCESSED/$BASENAME"
    
    # Notify
    osascript -e "display notification \"PDF sent to Birdy: $BASENAME\" with title \"🐦 Birdy\" sound name \"Glass\"" 2>/dev/null
done
