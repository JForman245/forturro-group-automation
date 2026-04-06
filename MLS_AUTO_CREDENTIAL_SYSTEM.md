# MLS Auto-Credential Management System

## 🎯 **System Overview**

Your MLS scraper now includes **automatic credential failure detection and management**. When login failures occur, the system will:

1. **Detect the failure automatically**
2. **Test current credentials** 
3. **Attempt auto-recovery** (clear cache, retry)
4. **Alert you via WhatsApp** if manual intervention needed
5. **Provide specific guidance** for fixing the issue

## 📁 **Files Created**

### Core Scripts:
- `scripts/mls-credential-manager.py` - Main credential management system
- `scripts/mls-scraper-with-auto-creds.py` - Enhanced scraper with auto-credentials
- `mls_credential_state.json` - Tracks credential health and failures

### Cron Job:
- **Name:** `mls-daily-scraper-auto-creds`
- **Schedule:** 6:00 AM daily (Eastern Time)
- **Function:** Runs enhanced scraper with credential monitoring

## 🚨 **Alert System**

When credentials fail, you'll receive a **WhatsApp message** to Forturro Group with:

```
🚨 MLS CREDENTIAL UPDATE REQUIRED

📊 Current Status:
- Consecutive failures: X
- Last successful login: [timestamp]
- Current username: [your username]

🔧 Required Actions:
1. Check if your CCAR password expired
2. Try manual login at: https://ccar.mysolidearth.com
3. Update credentials in .env.mls if needed
4. Run: python3 mls-credential-manager.py --update
```

## 🛠️ **Manual Commands**

### Test Credentials:
```bash
python3 scripts/mls-credential-manager.py --test
```

### Update Credentials:
1. Edit `.env.mls` with new password
2. Run: `python3 scripts/mls-credential-manager.py --test`

### Force Alert Test:
```bash
python3 scripts/mls-credential-manager.py --force-alert
```

### Run Enhanced Scraper:
```bash
python3 scripts/mls-scraper-with-auto-creds.py
```

## 🔄 **How It Works**

### Daily Workflow:
1. **6:00 AM:** Enhanced scraper starts
2. **Pre-flight Check:** Test credentials before scraping
3. **Run Scraper:** Execute MLS lead extraction (EXPIRED + WITHDRAWN ONLY)
4. **Post-flight Check:** Analyze logs for failures
5. **Auto-Recovery:** Attempt cache clearing if needed
6. **Alert & Guide:** WhatsApp notification if manual fix required

**Note:** Price reduction data collection has been DISABLED per user request.

### Failure Detection:
The system monitors for these failure indicators:
- "login failed - timeout"
- "authentication timeout" 
- "credential error"
- "access denied"
- "unauthorized"

### Recovery Attempts:
1. **Clear browser cache** (Safari)
2. **Retry login** with fresh session
3. **Test different login endpoints**
4. **Check for temporary CCAR outages**

## 📊 **Current Status**

Your **original scraper worked perfectly for 3 days** until **April 3rd** when CCAR authentication timeouts started occurring. This is likely due to:

1. **Password expiration** (CCAR requires periodic resets)
2. **Session timeout policy changes** 
3. **MFA/2FA updates**
4. **Account lockout** from failed attempts

## 🔧 **Immediate Next Steps**

1. **Manual Login Test:** Try logging into https://ccar.mysolidearth.com manually
2. **Check Email:** Look for CCAR password expiration notices
3. **Update Credentials:** If password expired, update `.env.mls`
4. **Test System:** Run `python3 scripts/mls-credential-manager.py --test`

## 📈 **Benefits**

✅ **Automatic failure detection** - no more silent failures  
✅ **Immediate WhatsApp alerts** - know about issues within minutes  
✅ **Self-recovery attempts** - handles temporary glitches automatically  
✅ **Specific guidance** - tells you exactly what to check  
✅ **Weekly health checks** - proactive credential monitoring  
✅ **Detailed logging** - full audit trail of all credential events  

Your MLS lead pipeline is now **self-monitoring and self-healing** for credential issues!

---

*Auto-Credential System deployed: 2026-04-05 12:07 EDT*