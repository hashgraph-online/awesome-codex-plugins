# setup-credentials — detect, credentials, authorize (React v7)

## 1. Detect project (package / config / framework)
- Confirm `package.json` has `react`. Identify the bundler → env prefix:
  - **Vite** → `.env`, `import.meta.env.VITE_*`
  - **Create React App** → `.env`, `process.env.REACT_APP_*`
  - **Next.js** → `.env.local`, `process.env.NEXT_PUBLIC_*`
  - **Astro (React)** → `.env`, `import.meta.env.PUBLIC_*`
  - **React Router (Vite)** → `.env`, `VITE_*`
- Reuse existing config: a prior `.cometchat/config.json` or already-set `*_COMETCHAT_APP_ID` → reuse, skip re-setup, don't re-provision or re-ask.

## 2. version_conflict — STOP gate
If `@cometchat/chat-uikit-react` is installed at a non-v7 major (e.g. v6), STOP. Surface it, reconcile (upgrade to v7, or load the matching-version skills), then continue. Never mix majors.

## 3. Credentials — fetch from the dashboard (offer it), or paste manually
> **The CLI is a DASHBOARD/API client only, loaded ON DEMAND (AUDIT-059).** The `@cometchat/skills-cli` tool does exactly THREE things: `auth` (dashboard login), `provision` (fetch an app's App ID/Region/Auth Key from the dashboard), and `config` (local cred state). It knows NOTHING about React/frameworks/UI Kit and does NOT write env files, detect the project, or generate code — **the SKILL owns all of that** (detection = §1 by reading the repo; env-writing = §4; codegen = the golden path). Only load the CLI when the user opts into fetching from the dashboard.

> **OFFER the dashboard fetch; don't default to manual paste (AUDIT-039).** When credentials are missing, present BOTH paths and default to the fetch: *"I can fetch your App ID / Region / Auth Key by logging into your CometChat dashboard (I'll load the CometChat CLI to do it), or you can paste them manually — which do you prefer?"* **Only if the user picks the fetch do you load/run the CLI** (below); a manual paste never touches the CLI. **Never silently skip to "paste them yourself," and never end the build with a "to finish, add credentials manually" TODO.**

> **The CLI.** Load it on demand with **`npx @cometchat/skills-cli@3` `<cmd>`** (public npm — no auth needed; `@3` pins the CLI major that matches the v5 skills). Below, `<cli>` = that full invocation. (Distinct from `@cometchat/skills`, which only installs these skills.)

**Fetch path (user opted in).** Let each command block — do NOT background or race them.
1. **Check auth:** `<cli> auth status --json` → `logged-in` | `logged-out`.
2. **Log in (if logged-out):** `<cli> auth login` — opens the dashboard in the browser (device-auth), polls, stores the bearer in the OS keychain. (`auth signup` for a brand-new account.) Surface terminal errors verbatim (`ACCESS_DENIED` / `EXPIRED` / `TIMEOUT` / `ABORTED`) and stop; don't retry silently.
3. **Pick the app — REUSE first, ASK with CURATED options, never auto-create:** if a `.cometchat/config.json` or env App ID already exists, use it and SKIP. Otherwise `<cli> provision list --json` returns the raw list — **the SKILL curates it; never dump a long table.** Present a selectable prompt of ≤4 options: the **TOP 3** apps ranked by relevance (framework match, then most-recent; name · region · App ID) **+ "Show all N apps"**; the free-text/"Other" answer = **paste an App ID/name manually**. Only on "Show all" list them all. No selectable prompts → the same as a numbered list (1–3, 4=show all, 5=manual) and WAIT. **NEVER dump all N as the primary prompt** (the 29-apps-in-a-table regression). **NEVER auto-create an app** — only on explicit request, confirming the name; zero apps → ask first.
4. **Fetch the credentials:** `<cli> provision use --app-id "<id>" --json` (or `provision run`) authenticates and returns `{ appId, region, authKey }` for that app **and writes a framework-neutral `.cometchat/config.json`** — it does NOT write any env file and takes NO `--framework` flag (that's the skill's job, §4). The Auth Key is returned so the skill can write it into the env; treat it as a secret (never echo it back to the user).
5. **Reuse existing:** a prior `.cometchat/config.json` or an already-set `*_COMETCHAT_APP_ID` → reuse, skip re-provision.

**Manual path** (user prefers, or the CLI can't run): Dashboard → Your App → Credentials → App ID, Region (`us`/`eu`/`in`), Auth Key (**dev only**). If neither path yields them, ASK and WAIT — never proceed with placeholders.

**Then the SKILL writes the env** from the config.json / returned creds — §4 (right prefix for the detected bundler) — and gitignores it. The CLI stops at "here are your credentials + a neutral config.json."

**Enable dashboard-gated features** (reactions, polls, translation, AI copilot, moderation, …) — the CLI does this (it's a dashboard/API op): `<cli> features list` shows the app's extensions + enabled state; `<cli> features enable <id>` / `disable <id>` flips the toggle via the management API (reads the App ID from `.cometchat/config.json`). Or do it manually in the **Dashboard** (Extensions / AI). Either way, YOU still wire the client component/prop (see `cometchat-react-v7-features`); the CLI only flips the dashboard toggle. Fetch current dashboard steps from the feature's `docs_topic`. (AUDIT-070 restored `features`.)

Production: mint a per-user **auth token** from your backend and use `loginWithAuthToken` — never ship the Auth Key to the client. The token endpoint is host code the SKILL scaffolds (or follow CometChat's docs); it is not a CLI step.

## 4. Env variables (three)
| Suffix | Required | Notes |
|---|---|---|
| `COMETCHAT_APP_ID` | yes | dashboard App ID |
| `COMETCHAT_REGION` | yes | `us` / `eu` / `in` |
| `COMETCHAT_AUTH_KEY` | dev only | replace with auth tokens in prod |

Prefix per bundler (Vite `VITE_`, CRA `REACT_APP_`, Next `NEXT_PUBLIC_`, Astro `PUBLIC_`). **The SKILL writes this env file** from the credentials (fetched into `.cometchat/config.json`, or pasted) — the CLI does not. **Then ENSURE the env file is gitignored (AUDIT-048): Vite/CRA scaffolds ignore only `*.local` (NOT `.env`), so an un-ignored `.env` with the Auth Key is a committable secret — verify/append `.env` to `.gitignore` for Vite/CRA/Astro; Next's `.env.local` is gitignored by default.** Restart the dev server after editing `.env`. Fail loud if any var is empty — an empty credential surfaces later as a cryptic `ERROR_API_KEY_NOT_FOUND`.

## 5. Authorize / verify
Credentials are valid when `CometChatUIKit.initFromSettings(settings)` resolves and `login()`/`loginWithAuthToken()` succeeds for a UID that exists in the app (see §6). Auth error on init/login → most commonly a **Region mismatch**; re-check the dashboard values. Do not render until login resolves.

## 6. Which user to log in as (the login UID) — do NOT invent one
`login(uid)` authenticates as a user that **must already exist** in your CometChat app; it does **not** create one. Never hardcode a guessed UID — even the current docs sample `cometchat-uid-1` is **not guaranteed to exist in this app**. Logging in as a missing UID fails (user-not-found) and the screen stays blank.
- **Never suggest a legacy/guessed sample UID.** Do **NOT** offer `superhero1` (or `superhero1..5`, `cc-user-*`, or any other remembered "classic sample" set) — those are NOT seeded in modern apps and only mislead the user. When you ASK, do not fabricate candidate UIDs from memory. The ONLY tentative suggestion allowed is `cometchat-uid-1..5`, and only labelled *"if this is a freshly-created app"* — never presented as a known-good login for THIS app.
- **Use a real UID:** Dashboard → your app → **Users** tab lists every UID. A freshly created / sample app is pre-seeded with sample users (`cometchat-uid-1`…`cometchat-uid-5`). ASK the user; prefer their own answer over any suggestion.
- **The login-UID prompt is DETERMINISTIC — ALWAYS present these SELECTABLE options, in this order (AUDIT-068/069):**
  1. **`cometchat-uid-1` — create-if-missing then login** *(dev, recommended for a fast start)*. Wire login as **create-if-missing then login** (`ensureDevUser` in `lifecycle.md`) so it's GUARANTEED valid on ANY app (fresh/sample/empty/custom). Don't "probe uid-1→uid-5": you can't check existence before login (`getUser` needs a session; we only hold the Auth Key), so probing = up to 5 login attempts — create-if-missing is ONE deterministic call. DEV-ONLY (prod → server-minted per-user tokens).
  2. **Paste your own UID** — for a real/custom app with existing users (Dashboard → Users); the free-text / "Other" answer. **No user is created** on this path.
  > This is a SKILL prompt (login-UID is the skill's job) — the CLI has no part in it. Keep it consistent run-to-run: option 1 (`cometchat-uid-1`, create-if-missing) must ALWAYS be present. Never suggest `superhero1`/legacy sample UIDs.
- **Create one (dev):** Dashboard → Users → **Add User** (set a UID, e.g. `alice`), then `login("alice")`. Programmatic creation (SDK `createUser` client-side, or the REST `POST /v3/users` with the REST API Key server-side) — fetch the exact signature/endpoint from docs; never ship the Auth Key to a client.
- **Production:** don't hardcode a sample UID. Per real end-user, create a matching CometChat user server-side (REST API + API key, using your own id as the UID), then log in with a per-user **auth token** from your backend → `loginWithAuthToken(token)` (§3).
