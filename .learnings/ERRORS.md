# Errors

Command failures and integration errors.

---

## [ERR-20260406-001] mls_daily_scraper

**Logged**: 2026-04-06T06:10:00-04:00
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
Daily MLS scraper cron fired at 6 AM but produced no output CSV for April 6

### Error
```
No mls_leads_20260406*.csv file found. Cron status shows "ok" but no scraper process visible and no output generated.
```

### Context
- Cron job `mls-daily-scraper-aut` (ID: 9ea7c293) ran at 6:00 AM ET
- Previous successful runs: April 3-5
- Relies on Chrome/Selenium + MLS CCAR login
- Possible causes: Chrome session issue, MLS login failure, silent script error

### Suggested Fix
Check script error handling — may need to add output logging to the cron job. Also verify MLS credentials haven't expired.

### Metadata
- Reproducible: unknown
- Related Files: mls_lead_scraper.py, scripts/lead-alert-monitor.sh

---
