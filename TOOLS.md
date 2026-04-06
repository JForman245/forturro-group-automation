# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### Follow Up Boss (CRM)

- **API Key:** stored in `.env.fub`
- **Auth:** Basic auth, API key as username, no password
- **Base URL:** `https://api.followupboss.com/v1`
- **Endpoints:** `/people`, `/notes`, `/events`, `/tasks`, `/deals`, `/me`
- **Usage:** `curl -s -u $FUB_API_KEY: https://api.followupboss.com/v1/people`
- **Account:** Jeff Forman (admin), forturro@followupboss.me
- **Connected email:** jeff@forturro.com (Google)
- **Calling/Texting:** enabled, (843) 994-2639

### GitHub CLI

- **Account:** JForman245  
- **Auth:** Token-based (keyring stored)
- **Scopes:** repo, gist, read:org, workflow
- **Usage:** `gh repo create`, `gh issue list`, `gh pr create`, etc.
- **Purpose:** Repository management, issue tracking, code deployment

### William Covey Media (Listing Photos)

- **Portal:** https://properties.williamcoveymedia.com/login
- **Login:** Info@forturro.com / 1801Oak!
- **Teams:** The Forturro Group (142 listings, admin), Scaturro (211 listings, member)
- **Photo CDN:** cdn.aryeo.com/listings/[address-slug]/resized/large/[filename].jpeg
- **Usage:** Login → Continue (pick team) → Listings → Search by address → Click listing → Get background-image URL from hero element
- **Note:** 2350 Chestnut (Orangeburg) was photographed by a different company, not William Covey

### Buffer (Social Media)

- **API Key:** stored in `.env.buffer`
- **API:** GraphQL at https://api.buffer.com/graphql (Bearer token auth)
- **Org ID:** 69cefe7b0f822245c9a50887
- **Channels:**
  - Facebook (The Forturro Group): 69cf01bbaf47dacb69826eef
  - LinkedIn (jformanmbrealtor): 69cf0080af47dacb69826bf8
  - Instagram (jforman_realtor): 69cf0271af47dacb69827091
- **Rules:** NEVER post without Jeff's explicit approval. Draft → show → approve → post.
- **Posting script:** `scripts/buffer_post.py` — always use this for posting. Handles image upload + all 3 channels.

#### ⚠️ Critical API Details (learned the hard way 2026-04-04)

- **Enum values are lowercase:** `mode: "shareNow"`, `schedulingType: "automatic"`. NOT uppercase.
- **schedulingType MUST be `"automatic"`** — `"notification"` requires a linked mobile device (Jeff doesn't have one) and will silently fail with `status: error`.
- **Images require a public URL** — Buffer fetches from URL, no direct upload. Use imgur (`Client-ID 546c25a59c58ad7`) or catbox.moe for hosting.
- **Duplicate detection is aggressive** — Buffer fingerprints on image URL + channel. Failed/errored posts count toward duplicates even after deletion. If hitting duplicate errors: upload image to a NEW URL (different host or re-upload) AND change the text.
- **Rate limit:** 15-minute windows. If you hit `RATE_LIMIT_EXCEEDED`, wait the full 15 min.
- **GraphQL union types:** `createPost` returns `PostActionPayload` union — must use inline fragments: `... on PostActionSuccess { post { id status } }`. Error types: `NotFoundError`, `UnauthorizedError`, `UnexpectedError`, `RestProxyError`, `LimitReachedError`, `InvalidInputError`.
- **Delete uses:** `DeletePostPayload` union with `DeletePostSuccess` and `VoidMutationError` (NOT `PostActionSuccess`/`NotFoundError`).
- **Always verify post status after creation** — a `post { id status }` response of `status: "sent"` is good. `status: "error"` means check `error { message rawError }`.

#### Channel-Specific Metadata

- **Facebook requires:** `metadata: { facebook: { type: "post" } }`
- **Instagram requires:** `metadata: { instagram: { type: "post", shouldShareToFeed: true } }` + at least 1 image
- **LinkedIn requires:** `metadata: { linkedin: {} }`

### Canva (Design)

- **API:** REST v1 at https://api.canva.com/rest/v1 (Bearer token auth)
- **Credentials:** `.canva_tokens.json` (access + refresh token), `.env.canva` (client ID/secret + MFA recovery codes)
- **Client ID:** OC-AZ1RXC8Oan-B
- **Account:** Jeff Forman
- **Scopes:** design:content:read/write, design:meta:read, asset:read/write, folder:read/write, brandtemplate:content:read, brandtemplate:meta:read, profile:read
- **Token expires:** Every 4 hours — refresh using client credentials + refresh token
- **Usage:** Create listing flyers, social media graphics, marketing materials, OMs
- **Rules:** Same as Buffer — NEVER publish without Jeff's explicit approval. Draft → show → approve.

### Meta (Facebook) Ads / Graph API

- **Access Token:** stored in `.env.meta`
- **Auth:** Bearer token
- **Base URL:** `https://graph.facebook.com/v22.0`
- **Usage:** `curl -s -H "Authorization: Bearer $META_ACCESS_TOKEN" https://graph.facebook.com/v22.0/me`
- **Account:** Jeff Forman (The Forturro Group)
- **Note:** Token may expire — if 401/190 errors, need to regenerate at developers.facebook.com Graph API Explorer
- **Rules:** Same as Buffer — NEVER run ads or post without Jeff's explicit approval.

### Edge TTS (Voice)

- **Package:** `edge-tts` (Microsoft Edge neural voices, free, unlimited)
- **Birdy's voice:** `en-US-JennyNeural` (friendly, considerate, warm)
- **Usage:** `edge-tts --voice "en-US-JennyNeural" --text "message" --write-media /path/to/output.mp3`
- **Send via Telegram:** `openclaw message send --channel telegram --target "8685619460" --message "caption" --media /path/to/output.mp3`
- **All voices tested:** Aria (confident), Ana (cute), Emma (cheerful), Jenny ✅ (friendly)

Add whatever helps you do your job. This is your cheat sheet.
