# Go Inside

Stage 3 in full: signing up, watching the messages, testing the upgrade and cancel flows, booking a demo, joining a creator's community, and questioning the chat bot. It shows what public pages never do: how the target actually activates, converts, sells, and keeps people.

## Contents
- Rules
- Setup
- Sign-up and onboarding
- The message sequence
- Upgrade and paywall
- The cancel flow
- The sales process
- Creator and community equivalents
- The chat and support probe
- Screenshots and logging

---

## Rules

Every action here is outward-facing. Confirm with the user before each sign-up, demo booking, community join, chat conversation, purchase, and cancellation. Approval for one doesn't cover the next.

- **Real identity only.** Sign up and book under the user's real name, real company or project, and an address on the user's domain. No invented personas, fake companies, or borrowed identities. The target will be able to see who signed up; make sure the user is fine with that.
- **Read the terms first.** Some terms bar competitors from signing up or using the product for competitive research. If they do, tell the user and let them decide. Never work around it.
- **No payment without explicit approval.** Use free plans, trials, and free tiers. Anything paid needs the user's yes with the amount, and a reminder to cancel.
- **No pretense with people.** Book a demo only if the user will say who they are when asked. Never claim a budget or a need the user doesn't have. Never message a creator, their team, or community members.
- **Take nothing that isn't yours.** No downloading other customers' or members' data, no security testing, no scraping inside the app or community, no shared logins.
- **Stop when asked.** If the target asks you to stop or closes the account, stop.

## Setup

- **Browser:** a browser tool this session exposes, with a clean profile so personalization and retargeting start from zero. No browser tool: give the user a numbered click-path and screenshot list to run themselves.
- **Inbox:** a dedicated address or labeled alias on the user's domain (for example `research@example.com`), used only for this teardown. Every message that arrives is evidence.
- **Folder:** `teardowns/<target-slug>/inside/`, with `screens/`, `emails.csv`, and `notes.md`.

## Sign-Up and Onboarding

Screenshot every screen from the landing page to the first result, and record:

| What | Why it matters |
|---|---|
| Sign-up options (SSO, email, magic link) and fields asked | Friction, and what they qualify on |
| Card required? Trial length and limits | The conversion model |
| Onboarding questions ("What's your role?", "Team size?") | How they segment, and likely what each segment sees next |
| Template, sample data, or blank start | How they get to a first result |
| Steps and minutes to the first result | Time to value, the number to beat |
| Checklists, tooltips, empty states, nudges | The activation playbook |
| Invite prompts | When they push the team loop |
| Upgrade prompts in the first session | How early they ask for money |

Compare with `$suede-onboarding` practice and note what they do that the user doesn't.

## The Message Sequence

Leave the account alone after sign-up and log every email, text, and push for 30 to 60 days in `emails.csv`:

`received_at,day,from,subject,preview,type,cta,offer,link`

- **Types:** welcome, onboarding tip, feature, social proof, nudge, trial-ending, upgrade offer, win-back, newsletter, release announcement, presale, sales outreach.
- **Day** is days since sign-up. The pattern of days is the sequence design.
- With approval, a second account that starts setup and stops halfway shows the behavior-triggered branch.
- Note which messages come from a person and whether replies reach a human.

Deliver the teardown on time with the sequence marked pending. Agree with the user how the rest gets collected: a rerun of this stage on a set date (Watch mode or a reminder) or the user forwarding the inbox export. Then update the playbook's Inside section. Hand the findings to `$suede-emails`.

## Upgrade and Paywall

Without paying, push against the free limits: hit the usage cap, try a paid feature, open the upgrade screen. Screenshot:
- The paywall copy, the plan it pushes, and any discount
- Whether the price differs from the pricing page (a sign of a test or geo pricing)
- Annual vs monthly framing and the default selection

Compare with `$suede-paywalls` and `$suede-pricing`.

## The Cancel Flow

On a trial or free plan, start a cancellation or downgrade and screenshot every step: the survey, save offers (discounts, pauses, downgrades), and the confirmation. Stop before final confirmation if the user wants to keep watching messages; cancel at the end. Compare with `$suede-churn-prevention`.

## The Sales Process

If the user approves a demo under their own name:

| Record | Example |
|---|---|
| Booking tool and form questions | 6 fields, asks budget and timeline |
| Routing | Instant calendar vs "we'll be in touch" |
| Speed to first response | 4 minutes, from a rep |
| Pre-call materials | Agenda, case study, a short video |
| What the demo covers | Feature order, the story, the proof shown |
| Pricing and discounting | Price shown, end-of-quarter offer |
| Follow-up cadence | Day 1, 3, 7 emails and a connection request |

Never record a call without the other side's consent. Take notes. Turn findings into the user's own demo with `$suede-sales-enablement`.

## Creator and Community Equivalents

For a creator, artist, band, or personal brand (see `target-types.md`), each with approval and under the user's real identity:

| Action | Record |
|---|---|
| Subscribe to the newsletter or mailing list | Welcome sequence, cadence, every ask (pre-save, merch, tickets, paid tier) |
| Pre-save or follow a release | The landing page, data asked, and every follow-up message |
| Join the public Discord, free membership tier, or fan club | Onboarding channels, rules, roles, rituals, announcement cadence. Read only: don't post, DM, or recruit |
| Walk the merch or ticket checkout | Bundles, order bumps, shipping thresholds, fees, presale codes. Stop before payment |
| Buy merch | Only with explicit approval and a set amount. Record packaging, inserts, and post-purchase messages |
| Buy tickets | Only if the user will attend, with approval |
| Walk a paid membership sign-up | Tiers, prices, perks. Stop before payment unless approved |

Never stream on loops, use bots, or open extra accounts. Never collect member names, handles, or messages.

## The Chat and Support Probe

Ask the site's chat bot or support the questions buyers ask, in the user's real name:
- "How are you different from [the user's company]?" and from the other main competitor
- "Why would I pick you over [category alternative]?"
- "What's included on the free plan?" and "Do you offer discounts?"

Bots often repeat the positioning script and objection handling word for word. Record answers verbatim with screenshots and label them **Observed**.

## Screenshots and Logging

- Name screenshots `NN-stage-what.png` (`03-onboarding-role-question.png`) so they sort into a storyboard.
- Every finding in the playbook links its screenshot or message row.
- Blur or crop personal details before sharing: staff names in emails, other customers' or members' data.
- List every account created, demo booked, community joined, and purchase made (with dates and whose name) in the method notes.
