#!/bin/bash
# Crexi & LoopNet Lead Auto-Responder
# Searches Gmail for new leads, adds to FUB, auto-responds with property info
# Runs via OpenClaw cron every 5 minutes

set -euo pipefail

WORKSPACE="/Users/claw1/.openclaw/workspace"
STATE_FILE="$WORKSPACE/memory/lead-responder-state.json"
GOG_ACCOUNT="jeff@forturro.com"

# Initialize state file if missing
if [ ! -f "$STATE_FILE" ]; then
  echo '{"processed_ids": []}' > "$STATE_FILE"
fi

# Get already-processed message IDs
PROCESSED=$(cat "$STATE_FILE")

# Search for Crexi leads (last 24h)
CREXI_RESULTS=$(GOG_ACCOUNT=$GOG_ACCOUNT gog gmail messages search 'from:notifications.crexi.com subject:"requesting Information" newer_than:1d' --max 10 --json 2>/dev/null || echo '{"messages":[]}')

# Search for LoopNet leads (last 24h) 
LOOPNET_RESULTS=$(GOG_ACCOUNT=$GOG_ACCOUNT gog gmail messages search 'from:leads@loopnet.com subject:"Lead for" newer_than:1d' --max 10 --json 2>/dev/null || echo '{"messages":[]}')

# Also catch LoopNet "favorited" notifications
LOOPNET_FAV=$(GOG_ACCOUNT=$GOG_ACCOUNT gog gmail messages search 'from:leads@loopnet.com subject:"favorited" newer_than:1d' --max 10 --json 2>/dev/null || echo '{"messages":[]}')

# Combine and process with Python
python3 << 'PYEOF'
import json
import os
import re
import subprocess
import sys

WORKSPACE = "/Users/claw1/.openclaw/workspace"
STATE_FILE = f"{WORKSPACE}/memory/lead-responder-state.json"
GOG_ACCOUNT = "jeff@forturro.com"

# Load state
with open(STATE_FILE) as f:
    state = json.load(f)
processed = set(state.get("processed_ids", []))

# Load FUB key
fub_key = None
with open(f"{WORKSPACE}/.env.fub") as f:
    for line in f:
        if line.startswith("FUB_API_KEY="):
            fub_key = line.strip().split("=", 1)[1]

if not fub_key:
    print("ERROR: No FUB_API_KEY")
    sys.exit(1)

# Parse email results
crexi = json.loads(os.environ.get("CREXI_RESULTS", '{"messages":[]}'))
loopnet = json.loads(os.environ.get("LOOPNET_RESULTS", '{"messages":[]}'))
loopnet_fav = json.loads(os.environ.get("LOOPNET_FAV", '{"messages":[]}'))

all_messages = []
for msg in crexi.get("messages", []):
    msg["_source"] = "Crexi"
    all_messages.append(msg)
for msg in loopnet.get("messages", []) + loopnet_fav.get("messages", []):
    msg["_source"] = "LoopNet"
    all_messages.append(msg)

new_leads = [m for m in all_messages if m["id"] not in processed]

if not new_leads:
    print("No new leads")
    sys.exit(0)

print(f"Found {len(new_leads)} new lead(s)")

import requests

def get_email_body(msg_id):
    """Fetch full email content"""
    result = subprocess.run(
        ["gog", "gmail", "get", msg_id],
        capture_output=True, text=True,
        env={**os.environ, "GOG_ACCOUNT": GOG_ACCOUNT}
    )
    return result.stdout

def parse_crexi_lead(body, subject):
    """Extract lead info from Crexi email"""
    info = {"source": "Crexi"}
    
    # Name from subject: "Jaxton Reber requesting Information on ..."
    name_match = re.search(r'^(.*?)\s+requesting\s+Information\s+on\s+(.*?)\s+in\s+', subject)
    if name_match:
        info["name"] = name_match.group(1).strip()
        info["property"] = name_match.group(2).strip()
    
    # Email from body
    email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', body)
    if email_match and "crexi.com" not in email_match.group(1) and "costar" not in email_match.group(1):
        info["email"] = email_match.group(1)
    
    # Phone from body
    phone_match = re.search(r'href="tel:([^"]+)"', body)
    if phone_match:
        info["phone"] = phone_match.group(1)
    
    # Property address from body
    addr_match = re.search(r'Regarding listing at ([^<]+)', body)
    if addr_match:
        info["address"] = addr_match.group(1).strip()
    
    # Message from body
    msg_patterns = [
        r'</p>\s*<p>\s*&nbsp;\s*</p>\s*<p>([^<]+)</p>\s*<p>\s*&nbsp;\s*</p>',
        r'interested',
    ]
    for p in msg_patterns:
        m = re.search(p, body, re.IGNORECASE)
        if m:
            info["message"] = m.group(1) if m.lastindex else "interested"
            break
    
    return info

def parse_loopnet_lead(body, subject):
    """Extract lead info from LoopNet email"""
    info = {"source": "LoopNet"}
    
    # Clean HTML
    clean = re.sub(r'<[^>]+>', '\n', body)
    clean = re.sub(r'\n\s*\n', '\n', clean)
    
    # Contact line: "name | phone | email | (Listing ID : xxx)"
    contact_match = re.search(r'([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*\(Listing ID\s*:\s*(\d+)\)', clean)
    if contact_match:
        info["name"] = contact_match.group(1).strip()
        info["phone"] = contact_match.group(2).strip().replace("+1 ", "")
        info["email"] = contact_match.group(3).strip()
        info["listing_id"] = contact_match.group(4).strip()
    
    # Property from subject
    prop_match = re.search(r'Lead for (.+)', subject)
    if prop_match:
        info["property"] = prop_match.group(1).strip()
    
    # Favorited format
    fav_match = re.search(r'(\w+\s+\w+)\s+favorited\s+(.+)', subject)
    if fav_match:
        info["name"] = fav_match.group(1).strip()
        info["property"] = fav_match.group(2).strip()
        info["message"] = "Favorited listing"
    
    # Address from body
    addr_match = re.search(r'(\d+\s+[^|<\n]+(?:St|Ave|Blvd|Dr|Rd|Way|Ct|Ln|Pl|Cir)[^|<\n]*\|\s*\w+,\s*\w{2}\s+\d{5})', clean)
    if addr_match:
        info["address"] = addr_match.group(1).replace("|", ",").strip()
    
    # Message from body
    msg_match = re.search(r'Hi,\s*(.*?)(?:Thanks|$)', clean, re.DOTALL)
    if msg_match:
        info["message"] = msg_match.group(0).strip()[:200]
    
    return info

def add_to_fub(lead_info):
    """Add lead to Follow Up Boss"""
    name_parts = lead_info.get("name", "Unknown").split(" ", 1)
    first = name_parts[0] if name_parts else "Unknown"
    last = name_parts[1] if len(name_parts) > 1 else ""
    
    data = {
        "firstName": first,
        "lastName": last,
        "source": lead_info["source"],
        "tags": ["Investor", f"{lead_info['source']} Lead"],
    }
    if lead_info.get("email"):
        data["emails"] = [{"value": lead_info["email"]}]
    if lead_info.get("phone"):
        data["phones"] = [{"value": lead_info["phone"]}]
    
    resp = requests.post(
        "https://api.followupboss.com/v1/people",
        auth=(fub_key, ""),
        json=data
    )
    
    if resp.status_code in (200, 201):
        person = resp.json()
        person_id = person.get("id")
        print(f"  ✅ Added to FUB: {lead_info.get('name')} (ID: {person_id})")
        
        # Add note about property interest
        property_name = lead_info.get("property", lead_info.get("address", "Unknown property"))
        note_body = f"{lead_info['source']} inquiry — interested in {property_name}."
        if lead_info.get("address"):
            note_body += f"\nAddress: {lead_info['address']}"
        if lead_info.get("message"):
            note_body += f"\nMessage: {lead_info['message']}"
        # Listing ID excluded per Jeff's preference
        
        requests.post(
            "https://api.followupboss.com/v1/notes",
            auth=(fub_key, ""),
            json={
                "personId": person_id,
                "subject": f"{lead_info['source']} Lead - {property_name}",
                "body": note_body
            }
        )
        return person_id
    else:
        print(f"  ❌ FUB error: {resp.status_code} {resp.text[:200]}")
        return None

def auto_respond(lead_info):
    """Send auto-response email with property info"""
    if not lead_info.get("email"):
        print(f"  ⚠️ No email for {lead_info.get('name')} — skipping auto-respond")
        return
    
    property_name = lead_info.get("property", lead_info.get("address", "the property"))
    first_name = lead_info.get("name", "").split(" ")[0] or "there"
    
    # Check if we have a Google Drive folder for this property
    address = lead_info.get("address", "")
    drive_link = ""
    if address:
        # Search for street number + street name
        search_term = " ".join(address.split(",")[0].split()[:4])
        result = subprocess.run(
            ["gog", "drive", "search", search_term, "--max", "5", "--json"],
            capture_output=True, text=True,
            env={**os.environ, "GOG_ACCOUNT": GOG_ACCOUNT}
        )
        try:
            files = json.loads(result.stdout).get("files", [])
            for f in files:
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    drive_link = f"\n\nHere's a folder with property documents and financials:\n{f['webViewLink']}"
                    break
        except:
            pass
    
    body = f"""Hi {first_name},

Thank you for your interest in {property_name}. I'd love to share more details with you.{drive_link}

Please feel free to call or text me anytime to discuss further or schedule a showing.

Best regards,
Jeff Forman
The Forturro Group
843-902-4325
Jeff@forturro.com"""

    result = subprocess.run(
        ["gog", "gmail", "send",
         "--to", lead_info["email"],
         "--subject", f"Re: {property_name} — The Forturro Group",
         "--body-file", "-"],
        input=body,
        capture_output=True, text=True,
        env={**os.environ, "GOG_ACCOUNT": GOG_ACCOUNT}
    )
    
    if result.returncode == 0:
        print(f"  ✅ Auto-responded to {lead_info['email']}")
    else:
        print(f"  ❌ Email failed: {result.stderr[:200]}")

def send_whatsapp_alert(lead_info):
    """Alert Jeff via WhatsApp"""
    source = lead_info["source"]
    name = lead_info.get("name", "Unknown")
    prop = lead_info.get("property", lead_info.get("address", "Unknown property"))
    phone = lead_info.get("phone", "N/A")
    email = lead_info.get("email", "N/A")
    
    msg = f"🚨 NEW {source.upper()} LEAD 🚨\n\n"
    msg += f"👤 {name}\n📞 {phone}\n📧 {email}\n🏠 {prop}\n\n"
    msg += "✅ Added to FUB + auto-responded"
    
    subprocess.run(
        ["openclaw", "message", "send",
         "--channel", "telegram",
         "--target", "8685619460",
         "--message", msg],
        capture_output=True, text=True
    )

# Process each new lead
for msg in new_leads:
    msg_id = msg["id"]
    source = msg["_source"]
    subject = msg.get("subject", "")
    
    print(f"\n📩 Processing: {subject}")
    
    body = get_email_body(msg_id)
    
    if source == "Crexi":
        lead_info = parse_crexi_lead(body, subject)
    else:
        lead_info = parse_loopnet_lead(body, subject)
    
    print(f"  Name: {lead_info.get('name', 'Unknown')}")
    print(f"  Email: {lead_info.get('email', 'N/A')}")
    print(f"  Phone: {lead_info.get('phone', 'N/A')}")
    print(f"  Property: {lead_info.get('property', lead_info.get('address', 'N/A'))}")
    
    # 1. Add to FUB
    fub_id = add_to_fub(lead_info)
    
    # 2. Auto-respond
    if fub_id:
        auto_respond(lead_info)
    
    # 3. Alert Jeff
    send_whatsapp_alert(lead_info)
    
    # 4. Mark as processed
    processed.add(msg_id)

# Save state
state["processed_ids"] = list(processed)[-200:]  # Keep last 200
with open(STATE_FILE, "w") as f:
    json.dump(state, f, indent=2)

print(f"\n✅ Processed {len(new_leads)} lead(s)")
PYEOF
