# Setup & credentials

## 1. Reuse before asking
A prior `.cometchat/config.json`, or an `environment.ts` that already has a non-empty `appId` → reuse it. Skip re-provisioning and do not re-ask.

## 2. Credentials — fetch through the CometChat MCP (offer it), or paste manually
> **Account actions go through the CometChat MCP server** — the `cometchat` server at `https://mcp.cometchat.com/mcp`. One endpoint: its docs tools need no sign-in; its `cometchat_*` tools manage the user's CometChat account and ask them to sign in on first use. There is no CLI to install. The MCP knows nothing about Angular — detection and writing the config are this skill's job (§3 Angular's config shape, then §4 gitignore).

> **OFFER the fetch; don't default to manual paste.** When credentials are missing, present BOTH paths and default to the fetch: *"I can fetch your App ID / Region / Auth Key from your CometChat account through the CometChat MCP, or you can paste them — which do you prefer?"* Never silently skip to "paste them yourself", and never end the build with an "add credentials manually" TODO.

**Fetch path (user opted in).**
1. **Check the connection:** call `cometchat_whoami`.
   - **No `cometchat_*` tools** → the `cometchat` server isn't added, or the host has only the docs tools. **Don't block: go straight to the manual path below** and offer once: *"Or connect your CometChat account and I'll fetch them: sign in to the `cometchat` MCP server (Claude Code: `/mcp` → Authenticate; Codex: `codex mcp login cometchat`; Cursor: Settings → MCP → Connect; ChatGPT: connect the CometChat app)."* Not added → add the `cometchat` server (per-agent commands: `references/docs-map.md`).
   - **Needs sign-in** (`unauthorized`, or the agent says `cometchat` needs a sign-in) → not signed in yet, or it expired; the docs tools still work. Same as above: manual path plus the sign-in offer. Use whichever the user does first.
   - **Connection or server error** (timeout, 404/5xx, "failed to connect"; not `unauthorized`) → the server is down. Retry at most once, don't ask for a sign-in, and switch to the manual path with a one-line note.
2. **Pick the app — REUSE first, ASK with CURATED options, never auto-create.** An existing `.cometchat/config.json` or an already-set `*_COMETCHAT_APP_ID` → reuse it and skip. Otherwise call `cometchat_list_apps`; **you curate the list — never dump it.** Offer at most 4 selectable options: the **top 3** most relevant apps (matching framework/product, then newest; name · region · App ID) + **"Show all N apps"**; the free-text answer = paste an App ID. No selectable prompts → a numbered list, then WAIT. **Never create an app unasked** — only on explicit request, with `cometchat_create_app` after confirming the name and region (it can't be changed later).
3. **Fetch the credentials:** `cometchat_get_app_credentials` with the chosen `app_id` → `app_id`, `region`, `auth_key`, plus ready-made `env` lines (`vite`, `nextjs`, `cra`). Write them yourself (§3 Angular's config shape, then §4 gitignore). The Auth Key is a secret: write it, never echo it back to the user.

**Manual path** (user prefers, or the MCP isn't available): Dashboard → Your App → Credentials → App ID, Region (`us`/`eu`/`in`), Auth Key (**dev only**). If neither path yields them, ASK and WAIT — never proceed with placeholders.

**Dashboard-gated features** (reactions, polls, translation, moderation filters, AI smart replies, ...): `cometchat_list_features` shows the app's extensions and AI features with their state; `cometchat_set_feature` turns one on or off — check `confirmed` in the result (false = CometChat accepted it but the app doesn't show it yet; tell the user to check the dashboard's Extensions page). AI features need an OpenAI key: only with a key the user gives you, `cometchat_set_openai_key`. Either way YOU still wire the client side (`cometchat-angular-v5-features`).

**Other account tasks the MCP handles** (ask before any change): test users (`cometchat_create_users`, `cometchat_create_auth_token`), groups, a server-side REST API key for a token endpoint or data import (`cometchat_create_api_key`, scope `fullAccess` — server env only, never client code), webhooks, push setup (`cometchat_get_push_setup`), moderation, roles, team and usage (`cometchat_get_usage`). Tools that change existing data return `confirmation_required` with a summary instead of acting: show it to the user, and call again with `confirm: true` only after they agree. Some changes (API keys, login tokens, the OpenAI key, webhooks, app settings, team invites, deletes) return `approval_required` with a link: give it to the user; they approve that exact change in the browser and give you a code; call again with the same arguments plus `approval_code`. Never open or approve the link yourself.

## 3. Write the config — Angular's shape
Angular resolves config at **build time** via file replacement. There is no `.env` and no bundler prefix.

```ts
// src/environments/environment.ts
export const environment = {
  production: false,
  cometchat: { appId: 'APP_ID', region: 'REGION', authKey: 'AUTH_KEY' },
};
```
```ts
// src/environments/environment.prod.ts — no authKey in production
export const environment = {
  production: true,
  cometchat: { appId: 'APP_ID', region: 'REGION', authKey: '' },
};
```
```json
// angular.json → the production configuration
"fileReplacements": [
  { "replace": "src/environments/environment.ts",
    "with": "src/environments/environment.prod.ts" }
]
```
Angular 15+ omits `src/environments/` from the scaffold — create it if absent.

## 4. ⚠️ After writing credentials, GITIGNORE the file (required step)
This is the Angular-specific trap, and it is worse than React's. A `.env` at least looks like a secret and many scaffolds ignore it. `src/environments/environment.ts` is **ordinary source that Angular's scaffold commits by default** — so the moment you write a real Auth Key into it, the developer's next `git commit -a` publishes a credential that can mint a session for **any user in the app**.

Shipping the file empty is right, but it does not solve this: the file becomes dangerous exactly when the skill does its job. So writing credentials and securing the file are **one action**, not two.

Do this immediately after writing the values:

1. **Add it to `.gitignore`:**
   ```
   /src/environments/environment.ts
   ```
2. **Commit a template instead** so a fresh clone still builds — without it the build fails with `Cannot find module '../environments/environment'`:
   ```ts
   // src/environments/environment.example.ts  (tracked, empty)
   export const environment = {
     production: false,
     cometchat: { appId: '', region: '', authKey: '' },
   };
   ```
3. **Tell the developer** the file is now ignored and that a new clone must copy the example across.
4. **Check whether it was already tracked** — `git ls-files --error-unmatch src/environments/environment.ts`. If it was, `git rm --cached` it as part of the same change, or the ignore rule does nothing.

> **Divergence from the docs.** `{DOCS_BASE}/ui-kit/angular/integration.md` shows the same `environment.ts` shape used here, but says nothing about the file being tracked or about gitignoring it. That is an omission, not permission — the guide is showing you where config goes, not making a security claim. Perform the steps above regardless.

`environment.prod.ts` stays **tracked**, with **`appId` and `region` POPULATED** and only
`authKey` empty. App ID and Region are not secrets — they identify the app; the Auth Key is
the secret, and production mints a per-user token server-side instead
(`cometchat-angular-v5-production`).

> ⚠️ **Leaving `appId`/`region` empty produces a build that succeeds and then does nothing.**
> `ng build` is green, but at runtime `main.ts`'s credential guard throws before
> `bootstrapApplication`, so `app-root` stays empty and the page is blank — with the thrown
> message visible only in the console. "The production build passed" is not evidence the
> artifact boots: serve `dist/` and confirm the conversation list actually renders.

**CI injection** — writing the file from CI secrets at build time — is a fine addition, but it is not an alternative: it does nothing for the local file the skill just wrote.

**If an Auth Key was already committed, it must be ROTATED in the dashboard.** Deleting it in a later commit does not help; it is in the history and in every clone.

## 5. Verify before building anything
```ts
const { appId, region, authKey } = environment.cometchat;
if (!appId || !region || !authKey) {
  throw new Error('CometChat credentials empty — check src/environments/environment.ts.');
}
```
Failing loudly here saves a long debug session: without it, init rejects and every list renders empty with no obvious cause. An empty credential otherwise surfaces later as a cryptic `ERROR_API_KEY_NOT_FOUND`. A failure on init or login is most often a **Region mismatch** — re-check the dashboard value.

## 6. Which UID to log in as — do NOT invent one
`login(uid)` authenticates as a user that **must already exist**; it does not create one. Logging in as a missing UID fails and the screen stays blank.

- **Never suggest a remembered "classic sample" UID** — `superhero1`, `cc-user-*` and similar are not seeded in modern apps and only mislead.
- The only tentative suggestion allowed is `cometchat-uid-1..5`, and only labelled *"if this is a freshly-created app"* — never presented as known-good for this app.
- **Ask the user.** Dashboard → your app → **Users** lists every UID. Prefer their answer over any suggestion.
- **When no UID is known, do not guess — use create-if-missing.** `ensureDevUser()` in `lifecycle.md` calls `CometChatUIKit.createUser()` then logs in, which is valid on any app without probing. Dev only; production uses a server-minted token.

## 7. Dashboard-gated features
Extensions and AI features are dashboard toggles. Flip them with the CometChat MCP (`cometchat_list_features`, `cometchat_set_feature` — check `confirmed`), or in the dashboard. Either way you still wire any client component — see `cometchat-angular-v5-features`.

## 8. Production
Mint a per-user **auth token** from your backend and call `loginWithAuthToken` — never ship the Auth Key to the browser. See `cometchat-angular-v5-production`.

## Checklist
- [ ] Reused existing config if present
- [ ] Offered dashboard fetch **and** manual paste; did not default to paste
- [ ] `environment.ts` written; `environment.prod.ts` has an empty `authKey`
- [ ] `fileReplacements` wired in `angular.json`
- [ ] **`environment.ts` gitignored immediately after writing credentials**, `environment.example.ts` committed, developer told
- [ ] If it was already tracked, `git rm --cached` applied in the same change
- [ ] Credentials validated at startup with a thrown error
- [ ] Login UID confirmed to exist (asked, not guessed)
