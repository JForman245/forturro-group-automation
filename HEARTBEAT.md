# Heartbeat Tasks

## Delivery Preference
- **Dave Ramsey + HomeLight lead alerts ONLY** → WhatsApp Forturro Group (`openclaw message send --channel whatsapp --target "120363029651955145@g.us"`)
- **Everything else** (Crexi/LoopNet alerts, reminders, status updates) → Telegram DM (`openclaw message send --channel telegram --target "8685619460"`)
- **NEVER send non-lead alerts to the Forturro Group WhatsApp**

## One-Time Reminders
- [x] **April 1, 7:00 AM ET** — Remind Jeff to cancel Twilio ✅ reminded
- [x] **April 2, morning** — Remind Jeff about ElevenLabs voice cloning setup (pricing, plan selection, voice clone recording) ✅ emailed
- [x] **April 2, morning** — Start building the local business dashboard ✅ built and running at localhost:8050 (deal pipeline, closed sales, current transactions, calendar, MLS leads, reminders). See memory/2026-04-01.md for spec.
- [x] **April 2, 10:00 AM ET** — Remind Jeff to review and edit the FUB automation triggers and action plan recommendations. Files: FUB_Action_Plan_Recommendations.md and FUB_Automation_Triggers_Plan.md ✅ reminded

## Ongoing Watches
- [ ] **Dave Ramsey / HomeLight Lead Alerts** — ✅ **REBUILT AS SHELL SCRIPT** (April 5, 9:05 AM). Now runs via `scripts/lead-alert-monitor.sh` on OpenClaw cron (Haiku, light-context, every 5 min). Script searches Gmail, diffs against `memory/lead-alerts-state.json`, and sends WhatsApp alerts to the Forturro Group chat. Zero heartbeat involvement needed — do NOT duplicate this check during heartbeats.
- [x] **WhatsApp Connection Stability** — ✅ **TELEGRAM ALERTS ENABLED** (April 5, 12:43 PM). Health monitoring via `scripts/whatsapp-health-monitor.sh` on OpenClaw cron (every 5 min). Tracks connection health and sends Telegram alerts to Jeff when issues detected. NO AUTO-RESTARTS, NO WHATSAPP GROUP MESSAGES.
- [ ] **CCAR RETS Response** — Check Gmail for reply to RETS/RESO API access request (sent April 1 to ccarinfo@ccarsc.org). Search: `from:ccarsc.org OR from:paragonrels OR subject:RETS newer_than:7d`. If reply found, alert Jeff via Telegram immediately with summary. Remove this item once resolved.
- [x] **Dotloop API Activation** — ✅ Activated! CS Tech sent API credentials (April 4, 3:30 PM). Jeff confirmed activation.
- [x] **MLS Scraper Results** — ✅ **FULLY OPERATIONAL** (April 5, 12:22 PM). Chrome WebDriver issues completely resolved with enhanced stability options. Auto-credential system working perfectly. Daily 6 AM scraper ready for production. Test scrape successful - 27 seconds runtime, clean CSV output.
- [x] **Tommy Campbell Reply** — ✅ Resolved. Tommy sent signed leases for 1704 Hillside #2 and #3. Jeff forwarded to Mark at QC Funding.
