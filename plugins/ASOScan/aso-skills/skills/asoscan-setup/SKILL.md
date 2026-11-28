---
name: asoscan-setup
description: When the user wants to set up ASOScan, for example to connect the ASOScan plugin or connector in ChatGPT or Claude, get an API access key for a coding agent, set up webhooks (including Slack or Microsoft Teams alerts), or connect Google Play Console or App Store Connect. Also use when the user mentions "connect ASOScan", "connect my ASOScan account", "get my API key", "set up webhooks", "send alerts to Slack", "connect my Play Console", "connect my App Store account", or "how do I hook this up". Works with no account and no key.
metadata:
  version: 1.3.7
---

# ASOScan Setup & Connect

Guides the user through configuring ASOScan: getting an **API key**, setting up
**webhooks** (incl. Slack / Teams), and **connecting** their Play Console / App
Store Connect accounts. **No API key needed to run this skill** — it's how they get
set up.

> ⚑ **Third-party UIs change — verify live, don't recite from memory.** For any
> step that happens **outside** ASOScan (Slack, Microsoft Teams / Power Automate,
> Google Play Console / Google Cloud, App Store Connect), **look up the current
> official instructions with web search before walking the user through them**, and
> prefer ASOScan's own up-to-date tutorials/docs where linked below. The
> **ASOScan-side** steps in this skill are current; the **external** steps you must
> confirm live each time.
>
> **Gating note:** webhooks and connections may not appear in every account —
> they're rolling out and depend on the plan/feature flags. If the user doesn't see
> a section, tell them the feature may not be enabled for their account yet.

---

## 0. Connect your ASOScan account (ChatGPT, Claude, Claude Code)

First check: can you call the ASOScan tools (for example `get_usage`)?

- **Yes**: the account is connected. Call `get_usage` (free) and tell the user how many API credits are left. Skip the API key section; it is only for coding agents without the tools.
- **No, and you are in ChatGPT or Claude**: tell the user to connect their ASOScan account. In ChatGPT, add the ASOScan plugin from the plugin directory. In Claude, add the ASOScan connector or plugin from the directory. Then sign in to ASOScan (or create an account; new accounts start with a free trial) and allow access. Allowing changes lets ASOScan add apps, keywords and competitors, save drafts, and post review replies the user approves.
- **No, and you are in Claude Code**: `claude plugin marketplace add ASOScan/aso-skills`, then `claude plugin install asoscan@asoscan`, then sign in when Claude Code asks. Or use an API key (section 1).
- **No, and you are in another coding agent**: use an API key (section 1).

To disconnect an assistant later: ASOScan **Settings → Connected AI apps → Disconnect**.

---

## 1. Get your ASOScan API key

Copy this checklist and tick each step:

```
API key setup
- [ ] 1. Create an ASOScan account + add at least one app
- [ ] 2. Settings → API access → New key name → Read-only / Read+write → Create key
- [ ] 3. Copy the key now (asosk_live_… is shown once)
- [ ] 4. export ASOSCAN_API_KEY="asosk_live_…"
- [ ] 5. Verify → expect 200 + your usage
```

**Details:**
1. Sign up at **asoscan.com** and add an app. The API is **owner-scoped** — it works
   on the apps in your account, so you need at least one.
2. **Settings → API access** → type a **New key name** → choose **Read-only** or
   **Read + write** (write lets the skills add keywords & competitors) → **Create
   key**. **Copy it now — `asosk_live_…` is shown only once.**
3. Set it as an environment variable:
   ```bash
   export ASOSCAN_API_KEY="asosk_live_…"     # bash/zsh (add to ~/.zshrc to persist)
   ```
   ```fish
   set -Ux ASOSCAN_API_KEY "asosk_live_…"     # fish
   ```
   ```powershell
   setx ASOSCAN_API_KEY "asosk_live_…"        # Windows PowerShell — open a new terminal after
   ```
4. Verify — a `200` with your usage means you're set:
   ```bash
   curl -s "https://asoscan.com/api/public/v1/usage" -H "Authorization: Bearer $ASOSCAN_API_KEY"
   ```
   A `401` names what went wrong (no key sent, wrong prefix, unknown or revoked key);
   a `403` means the plan doesn't include API access.

   Working from a clone of this repo? `bash scripts/asoscan-check.sh` does the same
   thing. It ships with the repo, not inside an installed skill, so the relative path
   only resolves from the repo root — use the `curl` above otherwise.

If the **API access** section isn't visible, the plan may not include API access —
see **asoscan.com/pricing**. Once the key works, come back and use any data skill.

---

## 2. Webhooks — get pushed events (Slack / Teams / your endpoint)

**What they are:** ASOScan can POST an event to a URL you own the moment something
happens — a rank drop, a competitor metadata change, a new opportunity, etc. — so
your team reacts without polling.

**Where:** ASOScan **dashboard → Settings → Webhooks**. Webhooks are **configured in
the dashboard, not via the public API** — a skill can't self-register them; guide
the user, don't `curl` it.

**Steps (ASOScan side) — the form is inline on that page:**
1. Go to **Settings → Webhooks**.
2. **Delivery format** — pick **Signed JSON** (your own HTTPS endpoint), **Slack**,
   or **Microsoft Teams**.
3. **Endpoint URL** — paste the destination (see per-format below).
4. **Events** — tap the event chips to choose which fire. The page shows the live,
   authoritative list (e.g. rank updated, app-sync completed, competitor metadata
   changed, review analyzed, new opportunities).
5. **Label** (optional) — a name like "Ops Slack relay".
6. Click **Add endpoint**, then **Send test** on the new row to confirm it lands.

**Signed JSON endpoint:** each delivery is **HMAC-SHA256 signed** — header
`X-ASOScan-Signature: t=<timestamp>,v1=<hex>` over `"{timestamp}.{rawBody}"`. Verify
it with a stdlib HMAC check (no SDK). The signing secret (`whsec_…`) is shown
**once** when you add the endpoint. For Slack/Teams there's no secret to manage —
the channel URL is the secret.

**Slack:** the user needs a Slack **Incoming Webhook URL** for the target channel,
then paste it into ASOScan with format = Slack.
> **Look up the current Slack steps live** (Slack changes this UI) — search Slack's
> official docs for creating an *Incoming Webhook* / Slack app with an incoming
> webhook. ASOScan also has a walkthrough: **asoscan.com/blog/send-aso-alerts-to-slack**.

**Microsoft Teams:** Teams delivery is built for the **Power Automate "Workflows"**
path (Microsoft is retiring the old Office 365 "Incoming Webhook" connector), so the
user creates a Workflow that "posts to a channel when a webhook request is received"
and pastes that workflow URL into ASOScan with format = Teams.
> **Look up the current Microsoft Teams / Power Automate steps live** — search
> Microsoft's official docs for the *"Post to a channel when a webhook request is
> received"* Workflows template. ASOScan walkthrough:
> **asoscan.com/blog/send-aso-alerts-to-microsoft-teams**.

Honesty: webhooks shorten your reaction time — they are **not** a ranking signal.

---

## 3. Connect Google Play Console or App Store Connect

Connecting a store account lets ASOScan read the app's own reviews, ratings and listing text and post the review replies the user approves.

1. Open the app in ASOScan and click **Connect** in the app header. (Settings → Connections only lists and disconnects accounts.)
2. Pick Google Play or App Store Connect and follow the wizard. The wizard shows the current steps and links the official Google and Apple guides; follow it rather than steps from memory.
3. For anything that happens on Google's or Apple's side, look up the current official instructions with web search before guiding the user.

If the user does not see **Connect**, the feature may not be enabled for their account yet.

Honesty: connected accounts read reviews, ratings and listing text and post approved review replies. ASOScan does not publish listing text to the stores.

## 4. Ad accounts

This skill does not cover ad accounts. Point the user to the ASOScan app.

---

## Related

- **aso-fundamentals** — learn ASO while you get set up (no key needed).
- The **data skills** — once the key is set: keyword-intelligence, keyword-opportunities,
  keyword-spy, competitor-analysis, review-insights, metadata-audit — your real numbers.

Full API reference + try-it console: <https://asoscan.com/api/developers>
