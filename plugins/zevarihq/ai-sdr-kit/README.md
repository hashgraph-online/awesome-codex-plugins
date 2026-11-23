# AI SDR Kit: the SDR harness for your AI

**Your AI can do outbound. Zevari teaches it how.**

Your AI (Claude, ChatGPT, Codex, OpenClaw, Hermes Agent or a Grok bot) is the brain. It can find people and write messages, but it has never run outbound. [Zevari](https://zevari.ai/?utm_source=github-kit) is the harness around it: an **AI Sales Director** that works out your outbound strategy from your account's own numbers and keeps revising it, the **playbooks**, **automations** that keep every play running, and the **sending engine** for LinkedIn and email.

Don't want to run it through your own AI? Zevari can run it for you with its own AI. Either way, you approve every play and nothing sends without your OK.

This kit is the free, open-source part: MIT licensed, free to fork.

---

## What does Zevari give my AI?

| Part | What it does |
|---|---|
| **AI Sales Director** | Studies your account's own numbers and tells your AI which play to run next: who to target, what to offer, which campaign, when to change course. It keeps checking the results and revises the plays. You approve each one. |
| **Playbooks** | The two guides in this kit: the outbound operating procedure and every LinkedIn and email sequence, step by step. |
| **Automations** | Once you approve a play, your AI sets it up as an automation and Zevari runs it every day, so your AI and your laptop don't have to babysit it. |
| **Sending engine** | LinkedIn connection requests, messages, InMail, likes, comments and email, paced inside LinkedIn-safe limits, with approvals built in. |

## What's in this kit?

| Skill | What your AI gets |
|---|---|
| [`agentify-outbound`](skills/agentify-outbound/SKILL.md) | The **Agentify Outbound SOP**: standing orders, a trust ladder and eight phases, from connecting Zevari to running on autopilot. |
| [`outbound-sequence-playbook`](skills/outbound-sequence-playbook/SKILL.md) | The **Outbound Sequence Playbook**: every LinkedIn and email sequence step by step, how to route each lead by ICP score and LinkedIn activity, and the exact campaign to build for each. |

Plus an MCP config that connects your AI to Zevari at `https://mcp.zevari.ai/mcp`, where the AI Sales Director, automations and sending live.

## How is it different from HeyReach, Apollo or Gojiberry?

Those are sending tools. You still have to know who to target, what to offer and which sequence to run, and you do it inside their dashboard. Zevari brings the judgment: its AI Sales Director picks the plays from your own numbers, your AI sets them up, and Zevari runs them. The playbook is open, so you can read, fork and change every step.

## Which AIs does it work with?

| Your AI | How to install |
|---|---|
| Claude Code | `/plugin marketplace add zevarihq/ai-sdr-kit`, then `/plugin install ai-sdr-kit@ai-sdr-kit` |
| Codex | `codex plugin marketplace add zevarihq/ai-sdr-kit`, then `codex plugin add ai-sdr-kit@ai-sdr-kit` |
| Claude or ChatGPT (chat apps) | [Add the Zevari connector](https://zevari.ai/linkedin-mcp?utm_source=github-kit), then ask it to load the `agentify-outbound` skill |
| Any agent that reads skills | `npx skills add zevarihq/ai-sdr-kit`, then connect it to Zevari (rows below) |
| OpenClaw | [Connect OpenClaw to Zevari](https://docs.zevari.ai/api/connect/openclaw?utm_source=github-kit), then give it [the SOP](https://zevari.ai/guides/agentify-outbound-sop.md) |
| Hermes Agent | [Connect Hermes to Zevari](https://docs.zevari.ai/api/connect/hermes-agent?utm_source=github-kit), then give it [the SOP](https://zevari.ai/guides/agentify-outbound-sop.md) |
| Grok bot or any other agent | [Bring your own agent](https://docs.zevari.ai/api/connect/bring-your-own-agent?utm_source=github-kit) with a Zevari access token, then give it [the SOP](https://zevari.ai/guides/agentify-outbound-sop.md) |

An AI that is already connected to Zevari doesn't need the files at all. It loads both guides itself with `skills_get` (slugs `agentify-outbound` and `outbound-sequence-playbook`) and asks the AI Sales Director for its plays with `sales_director_get`.

## How do I start?

Install the kit, then paste this into your AI:

```
This is my outbound operating procedure. Save it as OUTBOUND-SOP.md and keep one copy.
Read it. Follow the standing orders from now on. Do not send, connect, message, comment,
like, enroll or change any setting until I approve it. Searching and reading are allowed.
Ask Zevari's AI Sales Director what to set up first, then start with Phase 1.
Tell me what you need from me, one step at a time.
```

Your AI walks you through each phase one step at a time and asks before it does anything.

## What's free and what's paid?

| Free (this kit) | Paid (Zevari) |
|---|---|
| The SOP, the sequence playbook and the plugin, MIT licensed | The AI Sales Director: plays picked from your own numbers and revised as results come in |
| Your AI's own model for research, scoring and writing | Automations that run your approved plays every day |
| Forking and changing any of it | The sending engine for LinkedIn and email, with safety limits, approvals and the web dashboard |
| | Or Zevari runs the whole thing for you with its own AI |

There is no free LinkedIn connection. See [Zevari pricing](https://zevari.ai/pricing?utm_source=github-kit).

## What does my AI do after I install it?

It follows the SOP's eight phases:

1. **Connect:** connect Zevari, confirm your workspace and LinkedIn sender, change nothing.
2. **Business brain:** learn your business and offer from your own materials.
3. **Voice:** learn how you write from your real messages.
4. **ICP, list and scoring:** find your real buyer, build a list, train its scoring with you in batches of 25.
5. **Design the campaigns:** route each lead to a sequence from the playbook and draft the copy for your approval.
6. **Feedback loop:** learn from every correction, with a daily brief before you start work.
7. **Go live on approval:** start slow, inside the caps you approved.
8. **Graduate to autopilot:** only after you've approved its work unchanged for about a week.

Every job (sourcing, scoring, connection requests, DMs, cold email, replies) climbs its own trust ladder: off, read, draft, approve the batch, autopilot.

## How does it pick a sequence for each lead?

By ICP score and LinkedIn activity in the last 30 days:

| ICP score | Active on LinkedIn | Quiet on LinkedIn |
|---|---|---|
| 5 (Strong fit) | Every channel, 1 to 2 new a day | InMail and email |
| 4 (Strong fit) | LinkedIn-led sequence | Email-led sequence |
| 3 (Moderate fit) | Fit check by email | Fit check by email |
| 1 to 2 (Weak fit) | No contact | No contact |

The [playbook](skills/outbound-sequence-playbook/SKILL.md) has every sequence step by step.

## Can my AI write in a famous voice?

Yes. Install the Voice DNA skills (including Alex Hormozi, Josh Braun, Justin Welsh, Chris Walker and April Dunford; inspired by their public work, not affiliated with any of them):

- Claude Code: `/plugin marketplace add jpeslar1/john-peslar-ai-skills`, then `/plugin install voice-dna@john-peslar-ai-skills`
- Codex: `codex plugin marketplace add jpeslar1/john-peslar-ai-skills`, then `codex plugin add voice-dna@john-peslar-ai-skills`

Inside Zevari, your AI can also list voices with `skills_list` and apply one to a campaign.

## Is it safe for my LinkedIn account?

Nothing sends until you approve it, and the AI Sales Director's plays wait for your OK too. The SOP's first standing order is that your AI does nothing but read, search, score and draft until you say yes. Zevari runs all sending inside its [safety limits](https://zevari.ai/safety?utm_source=github-kit).

## More plays

Ready-made Claude Code workflows built on Zevari:

- [Weekly outbound pipeline](https://github.com/jpeslar1/linkedin-mcp-weekly-outbound-pipeline)
- [ICP lookalike discovery](https://github.com/jpeslar1/linkedin-mcp-icp-discovery)
- [Job-change trigger](https://github.com/jpeslar1/linkedin-mcp-job-change-trigger)
- [Inbound lead triage](https://github.com/jpeslar1/linkedin-mcp-inbound-lead-triage)
- [AE daily briefing](https://github.com/jpeslar1/linkedin-mcp-ae-daily-briefing)
- [Inbox zero triage](https://github.com/jpeslar1/linkedin-mcp-inbox-zero-triage)
- [Engagement pod](https://github.com/jpeslar1/linkedin-mcp-engagement-pod)
- [Lost-deal re-engagement](https://github.com/jpeslar1/linkedin-mcp-lost-deal-reengagement)
- [Event attendee enrichment](https://github.com/jpeslar1/linkedin-mcp-event-attendee-enrichment)
- [Webinar follow-up](https://github.com/jpeslar1/linkedin-mcp-webinar-followup)
- [Newsletter to pipeline](https://github.com/jpeslar1/linkedin-mcp-newsletter-to-pipeline)
- [Trade show pipeline](https://github.com/jpeslar1/linkedin-mcp-trade-show-pipeline)

## Keeping the guides current

The text of both skills comes from the public guides on zevari.ai. Run `scripts/sync.sh` to refresh them.

## License

[MIT](LICENSE)
