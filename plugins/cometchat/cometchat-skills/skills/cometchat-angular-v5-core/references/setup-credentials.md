# Setup & credentials

## 1. Reuse before asking
A prior `.cometchat/config.json`, or an `environment.ts` that already has a non-empty `appId` → reuse it. Skip re-provisioning and do not re-ask.

## 2. Credentials — OFFER the dashboard fetch, don't default to manual paste
When credentials are missing, present **both** paths and default to the fetch:

> *"I can fetch your App ID / Region / Auth Key by logging into your CometChat dashboard (I'll load the CometChat CLI to do it), or you can paste them manually — which do you prefer?"*

**Never silently skip to "paste them yourself", and never end the build with a "to finish, add credentials manually" TODO.** Only load the CLI if the user picks the fetch; a manual paste never touches it.

### The CLI — dashboard/API client only, loaded on demand
`@cometchat/skills-cli` does four things: `auth` (dashboard login), `provision` (fetch App ID/Region/Auth Key), `config`, and `features <list|enable|disable|ai-key>` (toggle dashboard extensions + AI) — §7 below uses that fourth one. It knows nothing about Angular, does **not** write env files, detect the project, or generate code — the SKILL owns all of that.

Load it on demand from public npm (`@3` pins the CLI major that matches the v5 skills):
```bash
npx @cometchat/skills-cli@3 <cmd>
```
No auth needed.

### Fetch path (user opted in)
Let each command finish — do not background or race them. `<cli>` = the full invocation above.

1. **Check auth:** `<cli> auth status --json` → `logged-in` | `logged-out`.
2. **Log in if needed:** `<cli> auth login` — opens the dashboard in a browser, polls, stores the bearer in the OS keychain. Surface terminal errors verbatim (`ACCESS_DENIED` / `EXPIRED` / `TIMEOUT` / `ABORTED`) and stop; do not retry silently.
> **If the browser is NOT already signed in to the dashboard — tell the user this BEFORE running the command.** `auth login` opens a URL carrying a one-time device-session id and then polls for up to **15 minutes**. If the browser is signed out, the dashboard redirects to its login page, and after signing in it drops the user on the dashboard home — **not back at the authorization URL**. The session is never authorized, the CLI polls until `TIMEOUT`, and it looks like "login worked but the CLI still can't see my apps".
>
> Say this up front: *"A browser window will open. If you're asked to sign in, sign in — then come back and open that same URL again (I'll print it). The CLI keeps waiting for up to 15 minutes."*
>
> - **Do NOT kill the command** while the user signs in — it is still polling, and re-running it invalidates the previous session id.
> - On `TIMEOUT` the CLI re-prints the URL. Opening it again while signed in completes immediately; that is the recovery, not a re-login.
> - `ALREADY_AUTHENTICATED` means the session id was already consumed — run `auth status` before assuming failure; you may already be logged in.

3. **Pick the app — reuse first, ask with CURATED options, never auto-create.** `<cli> provision list --json` returns the raw list; the SKILL decides how to present it. Rank by relevance (technology matching Angular, then most recent) and offer at most 4: the **top 3** (name · region · App ID) plus **"Show all N apps"**. The free-text/"Other" answer is the manual-paste path. Only list everything if they pick "show all". **Never dump 29 apps as the primary prompt.** Never create an app unprompted; zero apps → ask first.
4. **Fetch:** `<cli> provision use --app-id "<id>" --json` returns `{ appId, region, authKey }` and writes a framework-neutral `.cometchat/config.json`. It writes no env file. Treat the Auth Key as a secret — never echo it back.

### Manual path
Dashboard → your app → **Credentials** → App ID, Region (`us` / `eu` / `in`), Auth Key (**dev only**). If neither path yields them, ASK and WAIT — never proceed with placeholders.

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
Extensions and AI features are dashboard toggles. The CLI can flip them (`<cli> features list`, `<cli> features enable <id>`), or do it in the dashboard. Either way you still wire any client component — see `cometchat-angular-v5-features`.

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
