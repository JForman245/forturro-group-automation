# MLS Listing Sheet Workflow — CCAR Paragon 5

## System
- **MLS:** CCMLS (Coastal Carolinas MLS) via Paragon 5
- **URL:** https://ccar.paragonrels.com
- **Login:** Jeff Forman (session-based, browser login required)

## Steps to Pull a Listing Sheet

### 1. Navigate to Paragon MLS
- Open Safari → go to `https://ccar.paragonrels.com`
- Log in if not already (session lasts ~2 hours)

### 2. Search by Address
- Click the **Power Search** bar at the top of the page
- Type the property address (e.g. `330 45th Ave`)
- Press Enter — system loads search results

### 3. View Listing Detail
- The search results show matching listings
- The system displays the **"All Fields Detail"** view by default
- This includes: MLS #, status, price, address, beds/baths, sqft, lot size, year built, owner name, listing agent, schools, and a Google Map
- Navigate between results using the arrows (e.g. "4 of 40")

### 4. Print / Save as PDF
- Click the **Print** button in the Paragon toolbar (or `Cmd+P`)
- macOS Print dialog opens showing all 8 pages of the listing detail
- Settings: Portrait, US Letter, 100% scaling
- Click the **"PDF"** dropdown (bottom-left of print dialog)
- Select **"Save as PDF..."**
- Name the file with the property address (e.g. `330 45th Ave`)
- Choose save location (Desktop, Documents, etc.)
- Click **Save**
- PDF processes page by page and saves

## Output
- An 8-page PDF with the full "All Fields Detail" listing report
- Named by property address for easy reference

## Notes
- Default filename is "Spreadsheet Page" — always rename to the property address
- Author field shows as "CLAWD" (the Mac hostname)
- The listing sheet includes all MLS fields: property details, room dimensions, HOA, schools, agent info, remarks, and embedded Google Map
- Session timeout is ~2 hours — re-login if expired
- Power Search supports address, MLS #, agent name, etc.

## Automation Potential
- This workflow is browser-based (no API access yet — RETS/RESO request pending with CCAR)
- Could be automated via browser automation (Playwright/Puppeteer) once we have a working session flow
- For now: manual browser workflow or Jeff pulls the PDF and drops it to Desktop/email
