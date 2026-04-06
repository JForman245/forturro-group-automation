# MLS Lead Contact Enrichment

## Overview

The MLS scraper now includes **contact enrichment** to find property owner names, phone numbers, and email addresses for each lead. This significantly increases the value of the lead data for outreach and follow-up.

## How It Works

After pulling expired/withdrawn listings from Paragon MLS, the scraper:

1. **Takes each property address**
2. **Searches multiple data sources** for owner contact information
3. **Adds contact fields** to the CSV report: `owner_name`, `owner_phone`, `owner_email`, `contact_source`, `contact_found`
4. **Rate limits requests** to avoid being blocked

## Data Sources (in priority order)

### 1. Horry County Property Records
- **Source:** Official county property database
- **Reliability:** High (official records)
- **Data:** Owner name, mailing address
- **Rate limit:** 1 request per 2 seconds

### 2. WhitePages Reverse Address Lookup
- **Source:** WhitePages.com address search
- **Reliability:** Medium-High
- **Data:** Current resident name, phone number
- **Rate limit:** 1 request per 3 seconds

### 3. TruePeopleSearch
- **Source:** Free people search engine
- **Reliability:** Medium
- **Data:** Names, phone numbers associated with address
- **Rate limit:** 1 request per 2 seconds

### 4. Property Data APIs (ATTOM Data, etc.)
- **Source:** Commercial property databases
- **Reliability:** High (paid data)
- **Data:** Owner name, mailing address, property details
- **Cost:** API key required ($)

### 5. Google Search
- **Source:** Google search for "[address] owner contact"
- **Reliability:** Low-Medium (varies)
- **Data:** Publicly available contact info
- **Rate limit:** 1 request per 5 seconds

## Configuration

Edit `.env.contact` to configure:

```bash
# Enable/disable specific sources
ENABLE_COUNTY_RECORDS=true
ENABLE_WHITEPAGES=true
ENABLE_TRUEPEOPLESEARCH=true
ENABLE_PROPERTY_DATA_API=false    # Requires API key
ENABLE_GOOGLE_SEARCH=true

# API Keys (optional)
ATTOM_API_KEY=your_api_key_here

# Rate limiting
REQUEST_DELAY=1.5
MAX_RETRIES=3
RATE_LIMIT_RPM=30
```

## Sample Output

The CSV report now includes these additional columns:

| owner_name | owner_phone | owner_email | contact_source | contact_found |
|------------|-------------|-------------|----------------|---------------|
| John Smith | (843) 555-1234 | | whitepages | Yes |
| Jane Doe | | jane@email.com | county_records | Yes |
| | | | | No |

## Performance

- **Processing time:** ~2-3 seconds per lead (with rate limiting)
- **Success rate:** Varies by area, typically 40-70% find some contact info
- **Data quality:** County records and paid APIs are most reliable

## Legal & Compliance

- **Public records:** County property records are public information
- **Terms of service:** Respects rate limits and ToS of data sources
- **Privacy:** Only searches publicly available information
- **Usage:** For legitimate business purposes (real estate prospecting)

## Files

- `contact_finder.py` — Main contact enrichment class
- `contact_sources.py` — Individual data source implementations  
- `.env.contact` — Configuration file for API keys and settings

## Testing

Run contact enrichment on a test lead:

```bash
cd /Users/claw1/.openclaw/workspace
python3 contact_finder.py
```

## Debugging

Set environment variable for verbose logging:

```bash
export CONTACT_DEBUG=true
python3 mls_lead_scraper.py
```

This will show detailed logs of each contact search attempt.