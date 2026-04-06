# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260405-001] best_practice

**Logged**: 2026-04-05T14:39:00-04:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
Paragon MLS uses nested iframes — must navigate main → search frame → sub-iframe for document extraction

### Details
When automating MLS document extraction via Selenium, clicking "Associated Docs" loads documents in a sub-iframe (Reports/Report.mvc) within the search results frame. Scanning the parent frame returns 94 toolbar/menu links instead of actual documents. Must switch into the sub-iframe to find the document table.

### Suggested Action
Always check for sub-iframes after clicking navigation elements in Paragon. The document table has columns: Document, File Type, File Size, File Date.

### Metadata
- Source: error
- Related Files: mls_docs_extractor_v2.py
- Tags: mls, paragon, selenium, iframes
- Pattern-Key: mls.iframe_navigation

---

## [LRN-20260405-002] best_practice

**Logged**: 2026-04-05T14:00:00-04:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
Paragon Power Search dropdown option [0] is always a header — actual listings start at [1]

### Details
When using Power Search, the first dropdown option (index 0) is always the category header (e.g., "LISTING (10)") which contains "(ACTIVE)" in its text but clicking it loads wrong results. Must skip index 0 and match on options where text starts with a digit (MLS number).

### Suggested Action
Filter Power Search results: skip options where text doesn't start with a digit, then match on "(ACTIVE)" status.

### Metadata
- Source: error
- Related Files: mls_docs_extractor_v2.py
- Tags: mls, paragon, power-search
- Pattern-Key: mls.power_search_header

---

## [LRN-20260405-003] best_practice

**Logged**: 2026-04-05T13:30:00-04:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
Paragon CMA dialog blocks Associated Docs — must dismiss with OK button

### Details
If a CMA Presentation tab was previously open, clicking Associated Docs triggers a modal dialog: "Save open CMA(s)? This tab must be closed before another may be opened." Must click OK to dismiss before the docs view loads.

### Suggested Action
After clicking Associated Docs, always check for and dismiss the CMA dialog before scanning for documents.

### Metadata
- Source: error
- Related Files: mls_docs_extractor_v2.py
- Tags: mls, paragon, cma-dialog
- Pattern-Key: mls.cma_dialog_block

---

## [LRN-20260404-001] best_practice

**Logged**: 2026-04-04T15:00:00-04:00
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
Buffer API enum values must be lowercase and schedulingType must be "automatic"

### Details
Buffer GraphQL API requires lowercase enum values (e.g., mode: "shareNow", schedulingType: "automatic"). Using "notification" for schedulingType requires a linked mobile device and silently fails. Images require public URLs — use imgur for hosting. Duplicate detection is aggressive and counts failed posts.

### Suggested Action
Always use schedulingType: "automatic" and lowercase enums. Host images on imgur before posting.

### Metadata
- Source: error
- Related Files: scripts/buffer_post.py
- Tags: buffer, social-media, api
- Pattern-Key: buffer.api_enums
- Promoted: TOOLS.md

---

## [LRN-20260402-001] knowledge_gap

**Logged**: 2026-04-02T10:00:00-04:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
FUB API deals endpoint returns all deals including closed — filter by stageName not status

### Details
The Follow Up Boss /deals endpoint with status=Active returns all non-archived deals across all stages (Listed, Pending, Buyer Contract, Closed). Must filter by stageName to get specific transaction types. Date fields available: earnestMoneyDueDate, dueDiligenceDate, mutualAcceptanceDate, finalWalkThroughDate, projectedCloseDate, possessionDate.

### Suggested Action
Always filter FUB deals by stageName for stage-specific queries. Use userId=4 for Jeff's deals only.

### Metadata
- Source: conversation
- Related Files: forturro-dashboard/app.py
- Tags: fub, crm, api
- Pattern-Key: fub.deal_stage_filtering

---
