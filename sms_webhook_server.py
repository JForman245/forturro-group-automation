#!/usr/bin/env python3
"""
SMS Webhook Server for receiving messages from Jeff
Handles incoming SMS to Birdy's Twilio number
"""

from flask import Flask, request, Response
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/sms-webhook', methods=['POST'])
def handle_incoming_sms():
    """Handle incoming SMS messages"""
    
    # Extract message data
    from_number = request.form.get('From', '')
    to_number = request.form.get('To', '') 
    message_body = request.form.get('Body', '')
    message_sid = request.form.get('MessageSid', '')
    
    timestamp = datetime.now().isoformat()
    
    print(f"\n📱 INCOMING SMS [{timestamp}]")
    print(f"From: {from_number}")
    print(f"To: {to_number}")
    print(f"Message: {message_body}")
    print(f"SID: {message_sid}")
    
    # Log the message
    log_entry = {
        'timestamp': timestamp,
        'from': from_number,
        'to': to_number,
        'message': message_body,
        'sid': message_sid
    }
    
    # Save to log file
    with open('/Users/claw1/.openclaw/workspace/sms_log.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    # Auto-respond (optional)
    if 'test' in message_body.lower():
        response_msg = "🐦 Birdy here! SMS received successfully. Two-way messaging is working!"
    else:
        response_msg = f"🐦 Message received: '{message_body}' - I'll process this and respond via our secure channel."
    
    # TwiML response (optional auto-reply)
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_msg}</Message>
</Response>"""
    
    return Response(twiml_response, mimetype='text/xml')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {'status': 'SMS webhook server running', 'timestamp': datetime.now().isoformat()}

if __name__ == '__main__':
    print("🚀 Starting SMS webhook server...")
    print("📱 Ready to receive SMS messages at /sms-webhook")
    app.run(host='0.0.0.0', port=5000, debug=True)