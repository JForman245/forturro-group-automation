# Feature Requests

Capabilities requested by the user.

---

## [FEAT-20260405-001] mls_document_extractor

**Logged**: 2026-04-05T12:00:00-04:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Requested Capability
Automated extraction of Associated Documents from MLS Paragon listings by address

### User Context
Jeff needs to pull listing documents (GRI reports, disclosures, etc.) from Paragon MLS without manually logging in and clicking through. Each listing can have 1-10 documents.

### Complexity Estimate
complex

### Suggested Implementation
Built as mls_docs_extractor_v2.py — Selenium automation: login → Power Search → select ACTIVE listing → click Associated Docs → download all PDFs from document table.

### Resolution
- **Resolved**: 2026-04-05T14:39:00-04:00
- **Notes**: Fully working. Usage: `python3 mls_docs_extractor_v2.py "address"`

### Metadata
- Frequency: recurring
- Related Features: mls_lead_scraper, mls_listing_sheet

---

## [FEAT-20260405-002] dashboard_transactions

**Logged**: 2026-04-05T21:02:00-04:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Requested Capability
Dashboard showing active listings and pending transactions with closing dates, clickable to see due diligence timeline, earnest money dates, inspection dates, and closing date

### User Context
Jeff needs at-a-glance visibility into all transaction timelines — which deals are closing soon, what dates are coming up, what's overdue.

### Complexity Estimate
medium

### Suggested Implementation
Added to forturro-dashboard: new /api/transactions endpoint pulling from FUB, Active Listings card, Pending Transactions card (spans 2 columns) with click-to-expand timeline showing EM, DD, walk-through, closing, possession dates with color-coded status dots.

### Resolution
- **Resolved**: 2026-04-05T21:10:00-04:00
- **Notes**: Live at localhost:8050. 79 active listings, 33 pending deals with timeline view.

### Metadata
- Frequency: first_time
- Related Features: forturro-dashboard

---
