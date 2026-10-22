# Report template — `COMETCHAT_MIGRATION.md`

Write this file at the repo root, filled from the ledger. Leave out an empty section's rows, but keep its heading with "None." so the reader knows it was checked. Then END the chat reply with sections 3 and 5 pasted in full (SKILL step 11).

```markdown
# Stream (GetStream) → CometChat migration

**Branch:** cometchat-migration (created from <base>; <n> uncommitted files came along) · **Platform:** <framework> → CometChat <family label> · **Mode:** UI SDK | client | mixed
**Build:** ✅ passes (`<command>`) | ❌ <n> errors (listed below) · **Stream residue:** none | <paths>

## 1. Summary
<2–4 sentences: what the app did with Stream (Chat / Video / Feeds), what it does now, the headline removals.>

## 2. Migrated
| Stream feature | CometChat equivalent | Files |
|---|---|---|
| ChannelList + Channel/Window | Conversations + message pane (UI Kit) | src/chat/ChatPage.tsx, … |

## 3. Removed — not available in CometChat
| Feature | What it did | Removed from | What users lose | Evidence (features.json · `UI Kit:` docs query → result · `SDK:` docs query → result) | Closest CometChat alternative |
|---|---|---|---|---|---|
| Activity feed | Home timeline + follow buttons | src/feed/*, src/components/FollowButton.tsx, route /feed, server/feed.ts | The social feed | absent · UI Kit: `search_cometchat_docs "<feature> react ui kit"` → no page · SDK: `search_cometchat_docs "<feature> javascript sdk"` → no page | — |

### Dev/QA-only code removed (not user features)
| Code | What it did | Removed from |
|---|---|---|
| <debug panel / event simulator / screenshot harness> | <…> | <paths> |

## 4. Behavior changes (migrated, works differently)
- Livestream channels are now public groups; over 300 members, receipts and typing are off.

## 5. Your action items
1. Add your CometChat credentials (App ID, Region, Auth Key for dev) to `<untracked local env file>`. Never put them in a git-tracked file; placeholders are there now.
2. Create a REST API key and set `COMETCHAT_REST_API_KEY` on the server (the token endpoint + the data script).
3. Import your history: see `scripts/cometchat-migration/README.md` (dry run first).
4. **Messages older than ~6 months were NOT imported** (<n> skipped) — CometChat's default retention window (a CometChat-side limit, the same for any source — not a Stream property). To bring them over, purchase Extended Storage (contact CometChat sales), then re-run the import.
5. **Re-host media before deleting Stream** (<n> attachments). CometChat stores attachment URLs by reference, not the files, and Stream CDN URLs expire — re-host them to your own / CometChat media storage, or images and files break.
6. Enable in the CometChat dashboard: <extensions / AI features the migrated features need>.
7. Push: upload FCM/APNs credentials to CometChat (see the push setup).
8. Point your webhooks at the new receiver and pick the events.
9. Before production: switch from Auth Key login to server-issued auth tokens (if `devToken` was used).
10. Remove `STREAM_*` secrets from your CI and hosting env, then delete the Stream app after the cut-over.

## 6. Defaults taken (no questions were asked)
- <every decision made without asking, e.g. "UI SDK mode: replaced stream-chat-react with the CometChat UI Kit", "kept react-native-reanimated (used by other screens)">

## 7. Verification
- Build: `<command>` → <result>
- Residue search: `stream-chat|stream_chat|@stream-io|getstream|StreamChat|StreamVideo` → <result>
- Tests: <ran / not present / updated n tests, removed m tests of removed features>
- Pre-existing issues (were failing before the migration): <list or none>
```

Rules for the lists:
- Section 3's main table is for USER-facing features only. Debug panels, event simulators, doc-screenshot harnesses and demo settings go in the Dev/QA-only subsection, which needs no docs evidence. Moving a real user feature there to dodge the evidence rule is a defect.
- Every REMOVE row names the concrete files and UI entry points it touched, AND its evidence in this exact shape — `features.json`: <result> · `UI Kit:` `search_cometchat_docs "<feature> <platform> ui kit"` → <result> · `SDK:` `search_cometchat_docs "<feature> <platform> SDK"` → <result> (plus REST/live-fetch if used). A row whose cell lacks an explicit **SDK-level** query (the literal `SDK:` label or an `/sdk/` page) is graded as unevidenced, however right the removal is. "Removed feeds" alone is not enough. **The Evidence cell is MANDATORY on every row and must never be blank** — this includes narrower/partial removals (e.g. "Threads overview tab" while threaded replies stay): still cite the `features.json` + UI-Kit + SDK queries that show the specific surface has no equivalent. A row with an empty Evidence cell is an incomplete report.
- **Section 3 is a TABLE, never prose.** Write every removal as a row of the 6-column table above — not as bullets, paragraphs or a list, however well written. A removal outside a table row is ungradeable and the section is read as an incomplete report. (An empty section is the one exception: keep the heading with "None.")
- "Closest CometChat alternative" must be a real, documented capability (from `features.json` or the docs), or `—`. Never invent one.
- Order the action items by what unblocks running the app first: credentials first, then data, then production hardening.
