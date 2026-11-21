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

## 3. Credentials — fetch through the CometChat MCP (offer it), or paste manually
> **Account actions go through the CometChat MCP server** — the `cometchat` server at `https://mcp.cometchat.com/mcp`. One endpoint: its docs tools need no sign-in; its `cometchat_*` tools manage the user's CometChat account and ask them to sign in on first use. There is no CLI to install. The MCP knows nothing about React or your bundler — detection and writing the config are this skill's job (§4: the right prefix for the detected bundler, then gitignore).

> **OFFER the fetch; don't default to manual paste.** When credentials are missing, present BOTH paths and default to the fetch: *"I can fetch your App ID / Region / Auth Key from your CometChat account through the CometChat MCP, or you can paste them — which do you prefer?"* Never silently skip to "paste them yourself", and never end the build with an "add credentials manually" TODO.

**Fetch path (user opted in).**
1. **Check the connection:** call `cometchat_whoami`.
   - **No `cometchat_*` tools** → the `cometchat` server isn't added, or the host has only the docs tools. **Don't block: go straight to the manual path below** and offer once: *"Or connect your CometChat account and I'll fetch them: sign in to the `cometchat` MCP server (Claude Code: `/mcp` → Authenticate; Codex: `codex mcp login cometchat`; Cursor: Settings → MCP → Connect; ChatGPT: connect the CometChat app)."* Not added → add the `cometchat` server (per-agent commands: `references/docs-map.md`).
   - **Needs sign-in** (`unauthorized`, or the agent says `cometchat` needs a sign-in) → not signed in yet, or it expired; the docs tools still work. Same as above: manual path plus the sign-in offer. Use whichever the user does first.
   - **Connection or server error** (timeout, 404/5xx, "failed to connect"; not `unauthorized`) → the server is down. Retry at most once, don't ask for a sign-in, and switch to the manual path with a one-line note.
2. **Pick the app — REUSE first, ASK with CURATED options, never auto-create.** An existing `.cometchat/config.json` or an already-set `*_COMETCHAT_APP_ID` → reuse it and skip. Otherwise call `cometchat_list_apps`; **you curate the list — never dump it.** Offer at most 4 selectable options: the **top 3** most relevant apps (matching framework/product, then newest; name · region · App ID) + **"Show all N apps"**; the free-text answer = paste an App ID. No selectable prompts → a numbered list, then WAIT. **Never create an app unasked** — only on explicit request, with `cometchat_create_app` after confirming the name and region (it can't be changed later).
3. **Fetch the credentials:** `cometchat_get_app_credentials` with the chosen `app_id` → `app_id`, `region`, `auth_key`, plus ready-made `env` lines (`vite`, `nextjs`, `cra`). Write them yourself (§4: the right prefix for the detected bundler, then gitignore). The Auth Key is a secret: write it, never echo it back to the user.

**Manual path** (user prefers, or the MCP isn't available): Dashboard → Your App → Credentials → App ID, Region (`us`/`eu`/`in`), Auth Key (**dev only**). If neither path yields them, ASK and WAIT — never proceed with placeholders.

**Dashboard-gated features** (reactions, polls, translation, moderation filters, AI smart replies, ...): `cometchat_list_features` shows the app's extensions and AI features with their state; `cometchat_set_feature` turns one on or off — check `confirmed` in the result (false = CometChat accepted it but the app doesn't show it yet; tell the user to check the dashboard's Extensions page). AI features need an OpenAI key: only with a key the user gives you, `cometchat_set_openai_key`. Either way YOU still wire the client side (`cometchat-react-v7-features`).

**Other account tasks the MCP handles** (ask before any change): test users (`cometchat_create_users`, `cometchat_create_auth_token`), groups, a server-side REST API key for a token endpoint or data import (`cometchat_create_api_key`, scope `fullAccess` — server env only, never client code), webhooks, push setup (`cometchat_get_push_setup`), moderation, roles, team and usage (`cometchat_get_usage`). Tools that change existing data return `confirmation_required` with a summary instead of acting: show it to the user, and call again with `confirm: true` only after they agree. Some changes (API keys, login tokens, the OpenAI key, webhooks, app settings, team invites, deletes) return `approval_required` with a link: give it to the user; they approve that exact change in the browser and give you a code; call again with the same arguments plus `approval_code`. Never open or approve the link yourself.

## 4. Env variables (three)
| Suffix | Required | Notes |
|---|---|---|
| `COMETCHAT_APP_ID` | yes | dashboard App ID |
| `COMETCHAT_REGION` | yes | `us` / `eu` / `in` |
| `COMETCHAT_AUTH_KEY` | dev only | replace with auth tokens in prod |

Prefix per bundler (Vite `VITE_`, CRA `REACT_APP_`, Next `NEXT_PUBLIC_`, Astro `PUBLIC_`). **The SKILL writes this env file** from the credentials (returned by `cometchat_get_app_credentials`, or pasted) — the MCP does not write files. **Then ENSURE the env file is gitignored (AUDIT-048): Vite/CRA scaffolds ignore only `*.local` (NOT `.env`), so an un-ignored `.env` with the Auth Key is a committable secret — verify/append `.env` to `.gitignore` for Vite/CRA/Astro; Next's `.env.local` is gitignored by default.** Restart the dev server after editing `.env`. Fail loud if any var is empty — an empty credential surfaces later as a cryptic `ERROR_API_KEY_NOT_FOUND`.

## 5. Authorize / verify
Credentials are valid when `CometChatUIKit.initFromSettings(settings)` resolves and `login()`/`loginWithAuthToken()` succeeds for a UID that exists in the app (see §6). Auth error on init/login → most commonly a **Region mismatch**; re-check the dashboard values. Do not render until login resolves.

## 6. Which user to log in as (the login UID) — do NOT invent one
`login(uid)` authenticates as a user that **must already exist** in your CometChat app; it does **not** create one. Never hardcode a guessed UID — even the current docs sample `cometchat-uid-1` is **not guaranteed to exist in this app**. Logging in as a missing UID fails (user-not-found) and the screen stays blank.
- **Never suggest a legacy/guessed sample UID.** Do **NOT** offer `superhero1` (or `superhero1..5`, `cc-user-*`, or any other remembered "classic sample" set) — those are NOT seeded in modern apps and only mislead the user. When you ASK, do not fabricate candidate UIDs from memory. The ONLY tentative suggestion allowed is `cometchat-uid-1..5`, and only labelled *"if this is a freshly-created app"* — never presented as a known-good login for THIS app.
- **Use a real UID:** Dashboard → your app → **Users** tab lists every UID. A freshly created / sample app is pre-seeded with sample users (`cometchat-uid-1`...`cometchat-uid-5`). ASK the user; prefer their own answer over any suggestion.
- **The login-UID prompt is DETERMINISTIC — ALWAYS present these SELECTABLE options, in this order (AUDIT-068/069):**
  1. **`cometchat-uid-1` — create-if-missing then login** *(dev, recommended for a fast start)*. Wire login as **create-if-missing then login** (`ensureDevUser` in `lifecycle.md`) so it's GUARANTEED valid on ANY app (fresh/sample/empty/custom). Don't "probe uid-1→uid-5": you can't check existence before login (`getUser` needs a session; we only hold the Auth Key), so probing = up to 5 login attempts — create-if-missing is ONE deterministic call. DEV-ONLY (prod → server-minted per-user tokens).
  2. **Paste your own UID** — for a real/custom app with existing users (Dashboard → Users); the free-text / "Other" answer. **No user is created** on this path.
  > This is a SKILL prompt (login-UID is the skill's job) — no account tool is involved. Keep it consistent run-to-run: option 1 (`cometchat-uid-1`, create-if-missing) must ALWAYS be present. Never suggest `superhero1`/legacy sample UIDs.
- **Create one (dev):** Dashboard → Users → **Add User** (set a UID, e.g. `alice`), then `login("alice")`. Programmatic creation (SDK `createUser` client-side, or the REST `POST /v3/users` with the REST API Key server-side) — fetch the exact signature/endpoint from docs; never ship the Auth Key to a client.
- **Production:** don't hardcode a sample UID. Per real end-user, create a matching CometChat user server-side (REST API + API key, using your own id as the UID), then log in with a per-user **auth token** from your backend → `loginWithAuthToken(token)` (§3).
