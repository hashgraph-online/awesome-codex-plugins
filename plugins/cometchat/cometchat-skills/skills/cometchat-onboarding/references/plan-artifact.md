# plan-artifact — the template + the plan-completeness contract

The plan artifact is onboarding's DELIVERABLE. Because an onboarding skill emits no CometChat symbols, its "completeness oracle" is not a symbol catalog — it is this **plan-completeness contract**: the fixed set of sections the plan MUST contain, so every run of onboarding produces the same complete plan shape (not a lucky partial). This mirrors how `contracts.json` fixes the floor for a UI-Kit surface; here the floor is the plan itself. The matching machine-checkable contract lives in `contracts.json` as `onboarding-plan` (kind `plan`).

## The plan-completeness contract — the plan MUST contain all seven

| # | Section | What it fixes | Sourced from |
|---|---|---|---|
| 1 | **Discovery summary** | Every beat-1 signal, each a value or explicit `null` — framework · bundler · language · package manager · auth · styling · state · routing · SSR/CSR · existing CometChat · installed UI Kit / `version_conflict` · env file + prefix | repo read (package.json / lockfile / configs / source) |
| 2 | **Intent → capability map** | The confirmed archetype · modality · scope, TRANSLATED to CometChat capabilities, **each tagged UI Kit component or SDK method** (UI-Kit-first / SDK-fallback — flag SDK-backed features so the core wires them from the SDK docs) | beat-2 answers + `references/archetypes.md` |
| 3 | **Numbered actions** | The scoped build steps, in order — what the core will do | archetype + scope |
| 4 | **Files that will change** | The concrete paths/areas the build touches (additive — APPEND, never replace) | discovery + scope |
| 5 | **Packages** | The exact package(s) to install, with major pins (the core owns exact coordinates) | modality + framework |
| 6 | **Credential + auth strategy** | Dev Auth-Key vs prod server-minted auth token, CHOSEN from discovery (§archetypes credential heuristic) | `auth` signal |
| 7 | **Modify-or-approve gate** | An explicit invitation to EDIT or APPROVE — nothing is written before approval | always |

A plan missing any of the seven is **incomplete** — do not present it or hand off. (This is the onboarding analogue of "dropped a contract min_capability".)

## The template (fill every section; keep it concrete, not generic)

```md
## CometChat integration plan

### 1. What I found (discovery)
- Framework:      <value | null>
- Bundler:        <value | null>
- Language:       <TypeScript | JavaScript>
- Package mgr:    <npm | pnpm | yarn | bun | null>
- Auth:           <nextauth | clerk | firebase | auth0 | supabase | custom | null>
- Styling:        <tailwind | css-modules | mui | styled-components | chakra | null>
- State:          <redux | zustand | mobx | recoil | context | null>
- Routing:        <value | null>
- SSR/CSR:        <ssr | csr | islands | null>
- Existing CometChat: <yes (uikit <ver>) | no> · version_conflict: <none | detail>
- Env file/prefix:    <.env / VITE_ | .env.local / NEXT_PUBLIC_ | … | n/a>

### 2. What you want (intent → CometChat capabilities)
- Archetype: <1:1/marketplace | support | community | full-messenger | embedded>
- Modality:  <chat | calls | both>
- Scope:     <smallest surface | full combined app | embedded panel>
- Theming:   <auto/follow-OS light+dark (default) | fixed light | fixed dark> + <default tokens | match design system | brand palette | custom>
- → Capabilities: <the archetype's capability list from archetypes.md, e.g.
  "1:1 conversations · conversation list · message pane (send/receive + attachments) ·
   a 'Message seller' entry button">

### 3. What I'll do
1. <install the packages>
2. <credentials + env (dev Auth-Key OR prod token path — see §6)>
3. <init → login → render the scoped surface>
4. <wire the entry point into the existing app (routing/auth/state reuse)>
5. <match the existing design system>   ← if styling detected
6. <calls layer + permissions>          ← if modality includes calls
7. <…scoped to the archetype; smallest correct set>

### 4. Files that will change (additive — nothing replaced)
- <path/area 1>
- <path/area 2>
- <env file>
(APPEND only — your existing code is not rewritten.)

### 5. Packages
- <exact package@major> …   (the framework core owns the exact coordinates + pins)

### 6. Credential + auth strategy
- <Dev Auth-Key path — get moving now; do NOT ship the Auth Key to prod>
  OR
- <Prod server-minted auth token wired to <detected auth>: your backend mints a
  per-user CometChat auth token; frontend logs in with it. Map <app user id> → CometChat UID.>
(Credentials are fetched by the framework core at build time — it will OFFER to fetch the App ID/Region/Auth Key from the dashboard (loading the CometChat CLI on demand → `provision`) or let you paste them manually, then write the env itself; this section only states the dev-vs-prod strategy, not the fetch method.)

### 7. Approve or edit
Edit any part of this plan (change the archetype, add calling, narrow scope, switch the
credential strategy), or approve to start. **Nothing is written until you approve.**
```

## After approval — the scoped build directive (hand-off, not part of the plan the user sees)
On approval, hand the framework core a compact directive naming ONLY the scoped surface:
```
build-directive:
  core: cometchat-<family>-core        # the framework core for the detected framework
  archetype: 1:1/marketplace
  modality: chat
  scope: smallest 1:1 surface (message button → conversation ↔ message pane)
  credentials: dev-auth-key            # from plan §6
  touch: [src/features/chat/*, src/components/MessageSellerButton.tsx, .env]
  also-skills: []                      # only what the plan named (calls / customization / patterns …)
```
The core then does credentials + build + verify. For a framework with no shipped core (React Native, Vue, Flutter, iOS, Android — NOT React or Angular, which both ship one), DO NOT emit a directive — state the not-yet-built posture and offer the plan as the hand-off spec.

## Worked example (Next.js marketplace, chat only)

```md
## CometChat integration plan

### 1. What I found (discovery)
- Framework: Next.js (App Router) · Bundler: Turbopack/Webpack · Language: TypeScript
- Package mgr: pnpm · Auth: NextAuth · Styling: Tailwind · State: Zustand
- Routing: App Router · SSR/CSR: ssr · Existing CometChat: no · version_conflict: none
- Env file/prefix: .env.local / NEXT_PUBLIC_

### 2. What you want (intent → CometChat capabilities)
- Archetype: 1:1/marketplace · Modality: chat · Scope: smallest 1:1 surface
- → Capabilities: 1:1 conversations · conversation list · message pane (send/receive + attachments)
  · unread + presence · a "Message seller" button off the listing page

### 3. What I'll do
1. Install the React UI Kit + Chat SDK (major-pinned).
2. Credentials: prod server-minted auth token wired to NextAuth (Auth Key dev-only to start).
3. Client-only init → login → render the scoped 1:1 surface (App Router client boundary).
4. Add a "Message seller" button on the listing page → opens the conversation.
5. Match the Tailwind design tokens (hand to customization).

### 4. Files that will change (additive)
- src/app/(chat)/… (a client chat route)
- src/components/MessageSellerButton.tsx
- src/lib/cometchat/… (init/login helpers)
- .env.local
(APPEND only.)

### 5. Packages
- The resolved family's `kit_package` (+ `sdk_package` / `calls_package` where the row has them),
  read from `peers.yaml` — plus that kit's required peer deps. Never hardcode one family's packages.

### 6. Credential + auth strategy
- Prod server-minted auth token: a Next route mints a per-user CometChat auth token from the
  NextAuth session; the client logs in with it. Map the NextAuth user id → CometChat UID.
  Dev Auth-Key is fine locally but never shipped.

### 7. Approve or edit
Edit any part (add calling, widen to groups, change the credential path), or approve to start.
Nothing is written until you approve.
```
On approval → hand off to `cometchat-<family>-core` with the scoped directive above; pull in `customization` (Tailwind match) and `patterns` (Next App-Router client boundary) because the plan named them — nothing else.
