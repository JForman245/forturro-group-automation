# Free Lead Generation System for The Forturro Group

## Data Sources (All Free)

### 1. Horry County Public Records
- **Foreclosure filings** - scrape clerk of court website daily
- **Tax lien properties** - pull delinquent tax records 
- **Lis pendens notices** - legal notices of pending foreclosure
- **Divorce filings** - potential distressed sellers

### 2. Online Marketplaces  
- **Craigslist Charleston/Myrtle Beach** - FSBO keyword searches
- **Facebook Marketplace** - local property listings
- **OfferUp local** - people selling houses
- **Nextdoor** - neighborhood property posts

### 3. MLS Expired/Withdrawn
- **Daily MLS monitoring** - track expirations in your market area
- **Withdrawn listings** - often become FSBOs in 30-90 days
- **Price reduction tracking** - motivated sellers

## Automated Workflow

1. **Daily Data Collection** (6 AM cron job)
   - Scrape all sources for new properties
   - Extract: address, owner name, phone, price, situation
   - Remove duplicates, filter by criteria (price range, area)

2. **Lead Scoring** 
   - Recent foreclosure filing = Hot lead
   - FSBO + price reduction = Warm lead  
   - Tax lien + expired listing = Hot lead
   - Divorce + house = Warm lead

3. **Contact Research**
   - Cross-reference addresses with voter registration (public)
   - Skip trace phone numbers using free people search sites
   - Find property owner names from tax records

4. **CRM Integration**
   - Auto-add qualified leads to Follow Up Boss
   - Tag by source type (foreclosure, FSBO, expired, etc.)
   - Set follow-up reminders in Google Calendar

5. **Daily Lead Report**
   - Morning email with new qualified leads
   - Contact info, property details, lead score
   - Call script suggestions based on situation

## Technical Implementation

- **Python scripts** for data collection
- **Google Sheets** for lead tracking (free)
- **Follow Up Boss API** for CRM integration  
- **Free email** for notifications
- **Cron jobs** for automation

## Cost: $0/month
- All data sources are public/free
- Uses existing tools you already have
- No paid subscriptions required