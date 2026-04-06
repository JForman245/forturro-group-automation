# FUB + REALSCOUT AUTOMATION TRIGGER PLAN
## The Forturro Group — Jeff Forman

**Date:** April 1, 2026
**Goal:** Automatically trigger the right action plan based on lead behavior

---

## HOW IT WORKS

RealScout sends activity events into FUB. These events tell you exactly what a lead is doing:
- Viewed Property — they looked at a specific listing
- Viewed Page — browsing your site
- Visited Website — they came back to RealScout
- Seller Inquiry — someone wants a home valuation

You use FUB's Lead Flow + Smart Lists + Automations to route these leads into the right action plan automatically.

---

## TRIGGER MAP

### 🔥 TRIGGER 1: NEW BUYER LEAD (Any Source)
**What happens:** New lead comes in from RealScout, Zillow, Realtor.com, Ylopo, website, etc.
**Action:** Auto-assign → NEW BUYER action plan
**How to set it up in FUB:**
- Go to Admin → Lead Flow
- For each lead source (RealScout, Zillow, etc.), set the default action plan to your new Buyer plan
- Enable "Stop on Contact" — once you talk to them, the drip stops

### 🔥 TRIGGER 2: NEW SELLER LEAD
**What happens:** Someone requests a home valuation through RealScout, HomeLight, or your website
**Action:** Auto-assign → NEW SELLER action plan
**How to set it up in FUB:**
- Lead Flow for HomeLight → set action plan to Seller plan
- RealScout "Seller Inquiry" events → set action plan to Seller plan
- Any lead tagged "seller" → auto-apply Seller plan

### 🔥 TRIGGER 3: COLD LEAD COMES BACK TO LIFE
**What happens:** A lead who hasn't been active in 30+ days suddenly views 3+ properties in RealScout within a week
**Action:** Alert Jeff immediately (text + FUB task) + restart buyer action plan
**How to set it up:**
- FUB Smart List: Stage = "Stale" or "Dead" AND Last Activity < 7 days AND Source contains "RealScout"
- Automation: When someone moves from Stale → Active, send Jeff a text alert and reassign to Buyer plan
- This is your hottest signal — someone who ghosted you is now actively shopping again

### 🔥 TRIGGER 4: HIGH-INTENT BUYER (PROPERTY BINGE)
**What happens:** A lead views 5+ properties in a single session on RealScout
**Action:** Immediate text from Jeff + call task created
**Why:** Someone looking at 5+ homes in one sitting is ready to buy. They need a call, not an email drip.
**How to set it up:**
- FUB Smart List: Events in last 24 hours > 5 AND Event type = "Viewed Property"
- Automation: Create task "CALL NOW — hot buyer" + send Jeff alert
- Suggested text to lead: "Hey [Name] — saw you're looking at a bunch of places tonight. Want me to set up some showings this week?"

### 🔥 TRIGGER 5: REPEAT WEBSITE VISITOR (NOT YET A LEAD)
**What happens:** Someone visits your RealScout site multiple times but hasn't registered or inquired
**Action:** RealScout handles this with their AI nurture — but once they DO register, it flows into FUB as a new lead → Buyer plan auto-triggers
**Note:** Make sure your RealScout → FUB integration is passing ALL registrations, not just inquiries

### 🔥 TRIGGER 6: INVESTOR LEAD
**What happens:** Lead comes in looking at commercial, multifamily, or land
**Action:** Auto-assign → NEW INVESTOR action plan
**How to identify:**
- FUB tags: "investor", "commercial", "multifamily", "land"
- Lead source: specific campaigns you run targeting investors
- Manual tag by you or your team when they identify investor intent
**How to set it up:**
- FUB Automation: When tag "investor" is added → start Investor action plan
- This won't auto-trigger from RealScout (it's residential focused) — you'll tag these manually or from other lead sources

### 🔥 TRIGGER 7: POST-CLOSING TRANSITION
**What happens:** A deal closes
**Action:** Move to Post Closing plan (already have this — ID 7, 111 running)
**How to set it up:**
- FUB Automation: When deal stage = "Closed" → stop current action plan → start Post Closing plan
- This keeps the relationship alive for referrals and repeat business

### 🔥 TRIGGER 8: NURTURE TRANSITION (NO RESPONSE)
**What happens:** Lead completes the initial action plan (30/35/45 days) without responding
**Action:** Auto-move to long-term nurture plan
**Routes:**
- Buyer plan (30 days, no response) → *KTS Nurture Buyer (ID 30, already running 714)
- Seller plan (35 days, no response) → *KTS Nurture Seller (ID 31, already running 209)
- Investor plan (45 days, no response) → Monthly investor newsletter (build this)
**How to set it up:**
- Last step of each action plan = "Add to [Nurture Plan]"
- FUB handles this automatically when the plan completes

### 🔥 TRIGGER 9: HOME ANNIVERSARY
**What happens:** 1 year from a client's purchase date
**Action:** *KTS Home Anniversary plan triggers (ID 43, already set up)
**Why:** Generates referrals and repeat business. "Hey, happy 1 year in the house! How's everything going?"

### 🔥 TRIGGER 10: SPHERE RETURN TO WEBSITE
**What happens:** A past client or sphere contact comes back to RealScout and starts browsing
**Action:** Alert Jeff + personal reach-out task
**Why:** A past client browsing means they're either thinking about selling, buying a second home, or referring someone. Either way, you want to call them.
**How to set it up:**
- FUB Smart List: Stage = "Past Client" AND Last RealScout activity < 7 days
- Automation: Create task "Past client active on RealScout — call them"

---

## PRIORITY IMPLEMENTATION ORDER

**Phase 1 (Do This Week):**
1. Set new Buyer plan as default for all buyer lead sources in Lead Flow
2. Set new Seller plan as default for seller inquiry sources
3. Enable "Stop on Contact" for all three new plans

**Phase 2 (Next Week):**
4. Build Smart Lists for "Cold Lead Reactivation" (Trigger 3)
5. Build Smart Lists for "High-Intent Buyer" (Trigger 4)
6. Set up investor tagging workflow (Trigger 6)

**Phase 3 (Within 30 Days):**
7. Build nurture transition automations (Trigger 8)
8. Set up post-closing automation (Trigger 7)
9. Build sphere reactivation alerts (Trigger 10)
10. Create monthly investor newsletter for long-term nurture

---

## WHAT I CAN AUTOMATE FROM MY SIDE

Even without direct RealScout access, here's what I can do through FUB's API on a scheduled basis:

**Daily check (cron job):**
- Pull all RealScout events from last 24 hours
- Flag anyone who viewed 5+ properties (hot buyer alert → text you)
- Flag any stale leads that came back to life
- Flag any past clients browsing again

**Weekly digest:**
- Summary of all RealScout activity: who's active, who's hot, who went cold
- Leads that need manual follow-up
- Action plan performance stats

Want me to set up the daily monitoring cron job now?

---

## QUICK REFERENCE: YOUR REMAINING 23 ACTIVE PLANS

**Core Plans (Keep & Use):**
- New Buyer Plan (to be built)
- New Seller Plan (to be built)
- New Investor Plan (to be built)
- Post Closing Plan (ID 7) — 111 running
- *KTS Nurture Buyer (ID 30) — 714 running
- *KTS Nurture Seller (ID 31) — 209 running
- *KTS Barry Jenkins 3 Year Sphere (ID 42) — 233 running
- *KTS Home Anniversary (ID 43) — 9 running

**Source-Specific (Review — may consolidate into core plans):**
- *KTS New Buyer Lead (ID 19) — 243 running
- *KTS New Buyer Lead - zbuyer (ID 44) — 58 running
- *KTS New Seller - ZBuyer (ID 27) — 4 running
- *KTS New Zillow/Realtor/Trulia (ID 26) — 2 running
- STALE LEAD FLOW (ID 37) — 711 running

**Niche (Keep for now):**
- *KTS Renter to Future Buyer (ID 35) — 31 running
- *KTS Back to Website (ID 38) — 16 running
- *KTS Post Closing (ID 36) — 15 running

---

**Document prepared by Birdy 🐦**
**April 1, 2026**
