# archetypes — intent → CometChat capability map + repo-signal → recommended default

This is the translation layer for beats 2 and 3: it turns a **product archetype** into **CometChat capabilities** (the plan's "what you want"), and it turns **beat-1 repo signals** into the **recommended default** each intent question carries (the "make it easy + recommend" requirement). Capabilities named here are conceptual (chat surface / 1:1 / groups / calls / search / threads) — the framework core maps each to its own components on hand-off; onboarding does not name UI-Kit symbols.

## The five archetypes → capabilities

| Archetype | Product shape | CometChat capabilities (the plan's intent→capability) | Default modality | Default scope |
|---|---|---|---|---|
| **1:1 / marketplace** | Buyers ↔ sellers, requester ↔ provider — a "message this person" entry point off a profile/listing | 1:1 conversations · a conversation list · a message pane (send/receive, attachments) · unread + presence · a "Message <X>" entry button wired to open the conversation | chat | smallest 1:1 surface (a message button → a conversation ↔ message pane), NOT the full app |
| **support** | Customers ↔ support agents; often a launcher/widget in a corner, sometimes ticket-scoped | 1:1 (customer↔agent) conversations · a message pane · often **embedded** placement (a launcher/popup, not a full page) · optionally calls for escalation · agent-side may want a conversation list | chat | an embedded/widget support surface |
| **community / groups** | Members talk inside communities, channels, or rooms | **groups** · group conversations · group members + management/moderation · a message pane · often a groups/channels list · optionally group calls | chat | a groups + group-message surface |
| **full messenger** | A complete standalone chat app (the "everything" experience) | the whole combined experience: conversations + users/groups tabs · message pane · threads · search · calls · the full grow-target | both | the full combined app (the core's grow target) |
| **embedded** | Chat lives INSIDE an existing screen/flow, not as its own page (a side panel, drawer, or inline widget) | a scoped chat surface constrained to a container (a fixed-size panel/drawer), 1:1 or group as the host flow needs; minimal chrome | chat | a placement-constrained embedded surface |

> **Modality overlay.** Any archetype can be `chat` / `calls` / `both`. "Add calling" or a repo already using CometChat chat → recommend `calls`/`both`. Calls layer: 1:1 voice/video and/or group calls, incoming-call handling, and (on native) the platform permission config — the framework core + its calls skill own the details.

## Repo-signal → recommended default (beat 2 — infer, then let the user confirm)

Each question's recommendation comes from what beat-1 detected. Phrase every one as **"detected <signal> → recommend <default> — keep or change?"** — never a blank ask.

**Archetype (from routing/domain signals):**
- Marketplace/e-commerce signals — routes or dirs like `/products`, `/listings`, `/sellers`, `/checkout`; a product/seller/vendor model → **1:1 / marketplace**.
- Support/helpdesk signals — `/support`, `/help`, `/contact`, `/agent`, a tickets model, a widget/launcher pattern → **support** (embedded placement).
- Community/social signals — `/community`, `/groups`, `/channels`, `/rooms`, `/feed`, a groups/members model → **community / groups**.
- A greenfield/standalone app, or an explicit "build a chat app" → **full messenger**.
- Chat is clearly a secondary feature bolted onto an existing screen (dashboard/app shell with no obvious chat page) → **embedded**.
- No decisive signal → recommend the SMALLEST reasonable default (**1:1**) and say so; the user confirms or changes. (Do not stall — smallest-reasonable-default + flag, per `RULES.md` clarification only where genuinely blocking.)

**Modality:**
- Trigger was "add calling"/"add voice/video" → **calls** (or **both** if chat isn't present yet).
- Repo already has CometChat chat wired → **calls** (adding to existing).
- Otherwise → **chat**.

**Scope:**
- Default to the **smallest surface** that satisfies the archetype (the core's production-ready core surface for 1:1/support/community; a placement-constrained surface for embedded).
- Recommend the **full combined app** ONLY for **full messenger** or an explicit "the whole chat app" ask.

**Credential + auth strategy (feeds plan section 6):**
- A real auth system detected (`auth` ∈ nextauth/clerk/firebase/auth0/supabase/custom) → recommend the **prod server-minted auth-token** path, wired to that system (map the app's user id → the CometChat UID); note the dev Auth-Key is fine to start but must not ship.
- No auth detected (`auth: null`) → recommend the **dev Auth-Key** path to get moving, with an explicit note to add prod token auth before production.
- The framework core executes whichever is chosen (its `references/setup-credentials.md`); onboarding only decides + states it.

**Placement / SSR hints (feeds plan sections 3–4):**
- `styling` (tailwind/mui/…) → note "match the existing design system" as a plan step (hand to customization on build).
- **Theme MODE default = AUTO (follow the OS light/dark setting).** For a fresh app (no `styling` detected), recommend **auto** — the core syncs `theme` ↔ `prefers-color-scheme` (the kit ships light+dark but does NOT auto-follow the OS on its own; pack default per AUDIT-004). ALWAYS offer the auto/follow-system option in the design question — never a light-only or fixed-preset-only menu (AUDIT-042). Mode (auto/light/dark) and palette (default tokens / match design system / brand / custom) are independent — auto can pair with any palette.
- `ssr: ssr`/`islands` (Next App Router, Astro) → flag the client-boundary work in the plan (the chat surface is client-side; the core's patterns skill owns the directive).
- `state` (redux/zustand/context) → note where the "current conversation / logged-in CometChat user" state should live so it fits the app's existing store, not a new one.

## Notes
- These are **recommendations**, not decisions — the user confirms or overrides every one at the beat-4 gate.
- Onboarding names capabilities and archetypes; the **framework core** names components. Keep that split so this file stays platform-neutral and doesn't rot with UI-Kit changes.
