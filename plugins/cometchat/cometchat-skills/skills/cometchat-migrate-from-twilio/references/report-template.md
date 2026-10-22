# Report template — `COMETCHAT_MIGRATION.md`

Write this at the repo root from the ledger. Keep an empty section's heading with "None." Then END the chat reply with sections 3 and 5 pasted in full (SKILL step 11).

```markdown
# Twilio Conversations → CometChat migration

**Branch:** cometchat-migration (from <base>; <n> uncommitted files came along) · **Platform:** <framework> → CometChat <family label> · **Mode:** client/SDK (default) | UI Kit
**Build:** ✅ passes (`<command>`) | ❌ <n> errors (below) · **Twilio residue:** none | <paths>

## 1. Summary
<2–4 sentences: what the app did on Twilio Conversations (headless client + own UI), what it does now (CometChat Chat SDK behind the same UI, or UI Kit), the headline removals.>

## 2. Migrated
| Twilio feature | CometChat equivalent | Files |
|---|---|---|
| Conversations client + access-token login | CometChat init + `loginWithAuthToken` | src/chat/client.ts, server/token.ts |
| Conversation list / messages / participants | conversations + messages request builders + group members | src/chat/*, … |

## 3. Removed — not available in CometChat
| Feature | What it did | Removed from | What users lose | Evidence (features.json · docs query → result) | Closest CometChat alternative |
|---|---|---|---|---|---|
| Non-chat participants (SMS / WhatsApp / MMS) | Bridged the conversation to phone numbers via `addNonChatParticipant` | src/…, server/… | Reaching users over SMS/WhatsApp from the chat | Not in features.json · UI Kit `"sms whatsapp participant"` → no page · SDK `"non-chat participant sms"` → no page (Twilio omnichannel is vendor-specific) | — (use a separate SMS provider if still needed) |

## 4. Behavior changes (migrated, works differently)
- Presence/online model differs from Twilio's `notifiable`/`online` user flags.
- Conversations with exactly two participants are now 1:1 user conversations, not two-person groups.

## 5. Your action items
1. Add your CometChat credentials to an untracked env file (App ID, Region, Auth Key for dev). Placeholders are there now — never commit them.
2. Create a REST API key; set `COMETCHAT_REST_API_KEY` on the server (token endpoint + data script).
3. Import history: `scripts/cometchat-migration/README.md` (dry run first). Re-host media — Twilio media URLs expire.
4. Enable in the CometChat dashboard: <extensions / AI the migrated features need>.
5. Push: upload FCM/APNs credentials to CometChat.
6. Point webhooks at the new receiver; pick events.
7. Before production: server-minted auth tokens (already wired if a token server existed).
8. Remove `TWILIO_*` secrets from CI/hosting; close the Twilio Conversations service after cut-over.

## 6. Defaults taken (no questions were asked)
- <e.g. "client/SDK mode: kept the app's UI, swapped the data layer to the CometChat Chat SDK"; "skipped: <step> — <why>">

## 7. Verification
- Build: `<command>` → <result>
- Residue search: `twilio` (case-insensitive, excl. node_modules/dist/.git) → <result>
- Tests: <ran / none / updated n, removed m>
- Pre-existing issues (failing before the migration): <list or none>
```

Rules for the lists:
- Every REMOVE row names concrete files + UI entry points AND its evidence (features.json + both docs queries). Debug/QA-only code goes in a Dev/QA-only subsection, no evidence needed.
- "Closest CometChat alternative" must be a real documented capability or `—`. Never invent one.
- Order action items by what unblocks running the app first: credentials → data → production hardening.
