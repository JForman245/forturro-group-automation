# MLS Lead Scraper — Project Status

**Last Updated:** April 1, 2026 10:28 PM EDT

## What It Does

Automated daily scraper that logs into CCAR/Paragon MLS, pulls expired and withdrawn listings for the Grand Strand market, filters by target areas, **enriches with property owner contact information**, and saves a comprehensive CSV report.

## Current Status: ✅ WORKING

Tested and confirmed working as of 10:28 PM on April 1, 2026.

## Architecture

1. **Login:** SolidEarth SSO (ccar.mysolidearth.com) → click Email radio → enter credentials → SSO passes auth to Paragon
2. **Paragon MLS** (ccar.paragonrels.com) — the actual MLS system, uses Paragon 5
3. **Expired listings:** Pulled via Market Monitor link → Export CSV
4. **Withdrawn listings:** Pulled via Multi-Class Search form (Status=WD, Off Market Date last 30 days) → Export CSV
5. **Contact enrichment:** Search multiple sources for property owner names, phone numbers, emails
6. **Filtering:** Target areas only, rentals excluded
7. **Output:** Comprehensive CSV report with contact data in workspace

## Latest Run (April 1, 2026)

- **129 Expired** listings
- **427 Withdrawn** listings (last 30 days)
- **497 target-area leads** after filtering
- Breakdown: 216 residential, 184 condo/townhouse, 65 land, 21 commercial, 11 multi-family
- Report: `mls_leads_20260401_2228.csv`

## Files

- `mls_lead_scraper.py` — main scraper script
- `contact_finder.py` — contact enrichment system
- `contact_sources.py` — individual data source implementations
- `.env.mls` — MLS credentials (URL, email, password, target areas)
- `.env.contact` — Contact finder API keys and configuration
- `.env.fub` — Follow Up Boss API key
- `mls_leads_YYYYMMDD_HHMM.csv` — daily output reports with contact data
- `README_CONTACT_ENRICHMENT.md` — contact enrichment documentation

## Cron Schedule

```
0 6 * * * cd /Users/claw1/.openclaw/workspace && /usr/bin/python3 mls_lead_scraper.py >> mls_scraper.log 2>&1
```

Runs daily at 6:00 AM ET.

## Target Areas

Myrtle Beach, North Myrtle Beach, Little River, Longs, Conway, Surfside Beach, Garden City Beach, Murrells Inlet, Aynor, Loris

## Configuration

- **Exclude:** Rentals
- **Include:** Expired + Withdrawn (last 30 days)
- **FUB Upload:** Currently disabled (commented out), ready to enable

## What Was Fixed (April 1)

- Original scraper pointed at SolidEarth (SSO portal) instead of Paragon (actual MLS)
- Login form needed Email radio button clicked before entering credentials
- Field selectors were wrong (username → member_login_id, password → input[type='password'])
- Post-login redirect detection was looking for wrong page elements
- Search functions completely rewritten to use Paragon's Market Monitor and Search forms
- Withdrawn search added via Multi-Class search with Status=WD and Off Market Date filter
- .env.mls loading fixed (commas in area list broke shell env export)
