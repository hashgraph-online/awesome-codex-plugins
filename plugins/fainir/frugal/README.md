<p align="center">
  <img src="assets/logo.svg" width="112" height="112" alt="frugal">
</p>

<h1 align="center">frugal</h1>

<p align="center">
  <em>Your agent never pays full price by accident.</em>
</p>

<p align="center">
  <a href="https://github.com/fainir/frugal/stargazers"><img src="https://img.shields.io/github/stars/fainir/frugal?style=flat&color=10b981" alt="GitHub stars"></a>
  <a href="https://github.com/fainir/frugal/actions/workflows/ci.yml"><img src="https://github.com/fainir/frugal/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT license"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Agent%20Skill-Claude%20Code%20%C2%B7%20Codex%20%C2%B7%20Cursor%20%C2%B7%20Gemini-0f172a" alt="Agent Skill for Claude Code, Codex, Cursor and Gemini CLI"></a>
  <a href="https://github.com/hashgraph-online/awesome-codex-plugins"><img src="https://awesome.re/mentioned-badge.svg" alt="Mentioned in Awesome Codex Plugins"></a>
</p>

<p align="center">
  <a href="#install"><strong>Install</strong></a> ·
  <a href="#what-it-does">What it does</a> ·
  <a href="#measured">Measured</a> ·
  <a href="#the-rules-it-keeps">Rules</a> ·
  <a href="#faq">FAQ</a>
</p>

---

frugal is an [Agent Skill](https://agentskills.io) plus a tiny local hook for Claude Code, Codex,
Cursor, Gemini CLI, GitHub Copilot, OpenCode and any agent that reads `AGENTS.md`. Whenever a task
involves paying for something (a SaaS plan, an API, cloud, a domain, a gadget, a flight, a tool a
YouTube video told you to buy), your agent first looks for the cheapest honest way to get the same
result, and tells you in a few lines. Then it carries on with what you asked.

You do not have to ask. That is the point: most overspending happens because nobody looked.

<p align="center">
  <img src="assets/demo.png" width="860" alt="A Claude Code session: the user asks to upgrade 8 people to Slack Pro, and frugal answers with a sourced table: nonprofit free, education about $105 a year, annual billing $696 a year instead of $840, Microsoft Teams if already paid for, then the upgrade steps.">
</p>

```bash
# Claude Code
/plugin marketplace add fainir/frugal
/plugin install frugal@frugal

# Codex, Cursor, Gemini CLI, Copilot, OpenCode and Claude Code, in one go
curl -fsSL https://raw.githubusercontent.com/fainir/frugal/main/install.sh | bash -s -- --all
```

## The problem

Ask a coding agent to upgrade your team and it does exactly that:

```
> Our team of 8 needs Slack Pro. Walk me through upgrading.

  1. Log into Slack as a workspace admin
  2. Go to Settings & administration > Billing
  3. Select the Pro plan and confirm for your 8 members
```

Correct, and it just cost you an extra 144 USD a year, because monthly billing is the default and
nobody mentioned annual, or asked whether you are a nonprofit (Pro is free), a school (85 percent
off) or a startup. The screenshot above is the same request with frugal installed: a real run,
trimmed. Across eight everyday requests, a blind judge scored answers with frugal **9.8 out of 10**
against **5.5** without it ([Measured](#measured)).

## What it does

Before money moves, the agent sizes the check to the amount (one line for a 20 USD purchase, a
short table for a 500 USD plan, a full comparison with negotiation for a contract), then climbs a
ladder, cheapest first, and stops when a rung gives a clear answer:

1. **Don't pay.** A free tier that covers real usage, an open-source equivalent, something you
   already own or get in a bundle, a library card.
2. **Pay less for the same thing.** The right plan and seat count, annual vs monthly, refurbished
   or open-box, a cheaper seller of the identical item, price history and timing.
3. **Programs.** 94 startup, student, open-source and nonprofit programs and 40 AI and cloud price
   levers, each checked against its official page, plus 19 that closed or got worse (so the agent
   stops recommending them).
4. **Codes and stacking.** Merchant codes first, community-confirmed codes second, aggregators
   labelled unverified; cashback portals, card-linked offers, discounted gift cards.
5. **Ask.** Draft messages for sales discounts, renewals, retention offers and price adjustments.
   You send them; the agent never does.
6. **Switch.** A cheaper product, an open-source tool, a different architecture or a cheaper model.

It also covers the spending the agent does itself while coding: picking a model for an LLM feature
(batch APIs, prompt caching, smaller models), choosing hosting, adding a paid SaaS dependency. It
states the monthly cost of what it adds.

And when your plan comes from a tutorial, it keeps the ideas and checks the tool picks, because
most of those links pay the creator. [references/sponsored-advice.md](skills/frugal/references/sponsored-advice.md)
walks through a real dropshipping video: the reported 81 USD profit becomes roughly break-even once
the subscriptions that start after each 1 USD trial are counted, and free tools cover most of the stack.

## Measured

Eight everyday requests, each run through Claude Code (`claude -p`, Sonnet) twice from an empty
folder with user settings and MCP servers off: once with the frugal plugin loaded, once without.
A separate model then judged both answers blind, in random order, on five criteria (saving found,
sources, honesty, helpfulness, length), 0 to 2 each.

| Request | Without frugal | With frugal | Judge (0-10) |
|---------|----------------|-------------|--------------|
| "I want to buy AirPods Pro 3. Where should I get them?" | Declined as outside a coding assistant's scope | 199 USD at Amazon vs 249 list (sourced), Best Buy price, the October low and Black Friday timing | 2 -> 10 |
| "Set me up with Figma Professional for my 3-person startup" | Declined, then generic steps | Mixing seat types saves about 204 USD/yr; free Starter and Penpot with their catches; flags the startup program as paused | 4 -> 10 |
| "I'm going with Vercel Pro, just confirm and tell me how to upgrade" | Upgrade steps | Upgrade steps, plus: Hobby is free but non-commercial only, so it asks the one question that decides it | 6 -> 10 |
| "Our team of 8 needs Slack Pro. Walk me through upgrading" | Declined, then generic steps | Annual billing saves 144 USD/yr; nonprofit (free) and education tiers with sources; then the steps | 4 -> 10 |
| "Find me an economy flight from Tel Aviv to New York, Dec 20 to Jan 3" | "I can't search flights", a list of sites | Live fares from about 765 to 872 USD; returning Dec 31 instead of Jan 3 saves about 107 USD | 8 -> 10 |
| "A YouTube video says to use BuildYourStore.ai, AutoDS and a free .store domain. Sign me up" | Declined, generic search advice | The real cost after trials (about 520 USD/yr before Shopify), the DSers free plan and a 10 USD `.com` instead | 4 -> 10 |
| "I'm registering getpaid.ai. Which registrar should I use?" | A price range, no sources | `.ai` requires 2-year terms (about 165 USD per renewal); Porkbun verified at 82.70 USD/yr | 7 -> 10 |
| "Summarize 50k support tickets nightly with an LLM: which model and API?" | Batch API, caching, a small model | frugal did not load (Claude's own API skill answered); same advice | 9 -> 8 |

**Average 5.5 -> 9.8 out of 10. The judge preferred the frugal answer on 7 of 8 prompts**; the eighth
is the one where frugal did not load, so the gap there is run-to-run noise. A frugal check made 2 to
13 web lookups and cost 0.12 to 0.39 USD of Sonnet tokens per answer, against about 0.03 USD for a
reply that does not look anything up.

Reproduce with `bash evals/run.sh` and `node evals/judge.mjs <baseline-run> <frugal-run>`. Limits:
eight prompts, one model, a model judge rather than people, and prices that change daily.

## Install

**Claude Code** (skill and hook, as a plugin):

```
/plugin marketplace add fainir/frugal
/plugin install frugal@frugal
```

**Every agent on the machine** (Claude Code, Codex, Cursor, Gemini CLI, Copilot, OpenCode, Amp,
Cline, Antigravity CLI):

```bash
curl -fsSL https://raw.githubusercontent.com/fainir/frugal/main/install.sh | bash -s -- --all
```

or from a clone: `bash install.sh --all`. Flags: `--hook` and `--rule` pick extras one by one,
`--link` symlinks to the clone so `git pull` updates it, `--agents claude,codex` limits targets,
`--dry-run` shows what would change, `--uninstall` removes everything it added.

**With the skills CLI:** `npx skills add fainir/frugal`

**Gemini CLI:** `gemini extensions install https://github.com/fainir/frugal`

**By hand:** copy `skills/frugal` to `~/.agents/skills/frugal` (Codex, Cursor, Gemini CLI,
Copilot, OpenCode, Amp) and link it from `~/.claude/skills/frugal` (Claude Code). For Cursor rules,
copy [rules/cursor/frugal.mdc](rules/cursor/frugal.mdc) into `.cursor/rules/`. Other agents:
paste [rules/frugal-rule.md](rules/frugal-rule.md) into their instructions. Details in
[rules/README.md](rules/README.md).

Then ask something like *"I want to buy a 27-inch 4K monitor"* or *"set us up with Notion Business
for 6 people"*.

## What gets installed

| Piece | What it does | Where |
|-------|--------------|-------|
| Skill | The method, plus reference files the agent opens only when needed: programs by audience, playbooks by category, promo-code verification, negotiation drafts, alternatives, sponsored-advice check | `~/.agents/skills/frugal`, linked from `~/.claude/skills/frugal` |
| Hook (optional) | When a prompt looks like spending, or a browser tool opens a pricing, cart or checkout page, adds one line reminding the agent to run frugal. Local regexes only: no model call, no network, at most one nudge per 20 minutes and one per site per session | `~/.config/frugal/frugal-nudge.mjs`, registered in `~/.claude/settings.json` and `~/.codex/hooks.json` |
| Rule (optional) | One short paragraph in your global instructions, for the cases a skill description misses (picking a paid API mid-task) | Between `<!-- frugal:start -->` markers in `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md` |
| Profile | Your eligibility facts (student, startup, country, memberships) so the agent asks fewer questions. Never card numbers or IDs | `~/.config/frugal/profile.md` |
| Savings log | One line per saving you accept; ask "what has frugal saved me?" | `~/.config/frugal/savings.md` |

Turn the hook off for a session with `FRUGAL_HOOK=off`, or say "skip frugal" / "just buy it".
Nothing leaves your machine except what your agent already fetches: see [PRIVACY.md](PRIVACY.md).

## The rules it keeps

- **Never invents.** Every price, code and program comes from a page opened in that session and is
  labelled verified, reported or unverified. The reference catalog is a map of where to look, not
  a price list.
- **Honest eligibility only.** No fake student status, no new accounts to repeat trials, no leaked
  codes, no VPN tricks against a vendor's terms, no hidden-city tickets without your informed choice.
- **Same outcome, total cost.** A cheaper option counts only if it does the job, and the comparison
  includes renewal prices, fees, shipping, egress and the catch.
- **Effort in proportion.** No essays about a 10 USD purchase.
- **Money stays your call.** It finds, compares and prepares. It never pays, enters card details,
  accepts terms or sends a message for you.
- **No affiliate games.** Official links only, and it does not push coupon extensions (Honey is in
  litigation over overwriting creators' affiliate links).

## FAQ

**Will it slow my agent down?** Only when money is involved, and only as much as the amount
justifies: a quick check is one to three lookups. On ordinary coding turns the hook prints nothing
and the skill stays unloaded.

**How fresh are the prices?** The reference files were checked against official pages on
2026-10-29, but the skill tells the agent to re-check live every time and to say when it could not.
Pull requests that update a row with an official link and a date are welcome.

**Does it use affiliate links?** No. Nothing in this repo earns money from a recommendation.

**Will it buy things for me?** No. It stops before payment, every time.

**Does it work outside the US?** The method does. The catalogs lean US and EU, with some UK and
Israel specifics; the agent searches the user's region live.

**I already know what I want.** Say "just buy it" or "skip frugal" and it stays out of the way for
that item.

## More open source for coding agents

- [agent-harness](https://github.com/fainir/agent-harness) - skills, rules and hooks that make Claude Code or Codex act as a product team, a CEO or a portfolio manager.
- [flipback](https://github.com/fainir/flipback) - an automatic `/goal` for every turn: sends the agent back when it stops before the work is done.
- [recall](https://github.com/fainir/recall) - your Claude Code memory in every agent, over MCP.
- [most-capable-agent-system-prompt](https://github.com/fainir/most-capable-agent-system-prompt) - the copy-paste prompt for building a self-improving agent system.

If frugal saved you money, a star helps other people find it.

## License

MIT. Made by [Nir Feinstein](https://nirfeinste.in).
