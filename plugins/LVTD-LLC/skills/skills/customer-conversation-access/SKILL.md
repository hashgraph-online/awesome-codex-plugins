---
name: customer-conversation-access
description: Find and frame customer conversations through warm intros, communities, casual chats, events, advisors, landing-page replies, and meeting requests. Use when a team needs people to interview, cold outreach is failing, a meeting ask sounds needy or pitchy, or customer discovery needs a credible reason to talk.
license: MIT
compatibility: Codex, Claude Code, and other Agent Skills-compatible clients.
metadata:
  version: "0.1.3"
  displayName: Customer Conversation Access
  category: Marketing
  tags: customer-discovery,outreach,startups,interviews,research
---

# Customer Conversation Access

Use this skill to help teams get into useful customer conversations without
turning every interaction into a formal interview or sales pitch. The best
access path depends on where the target segment already spends time and who can
credibly introduce the team.

## Source Traceability

Primary source: The Mom Test by Rob Fitzpatrick, especially chapters 4, 6, and
7. Guidance is paraphrased for this MIT repo; authoring notes used converted
EPUB lines 2176-2362 and 2791-3610.

## Access Paths

| Path | Use When | Watch For |
|------|----------|-----------|
| Warm intros | Someone credible can introduce the team | Make the ask easy and specific |
| Existing communities | Customers gather in events, forums, meetups, Slack, Discord, or associations | Participate before extracting value |
| Casual chats | The context naturally touches the problem | Keep the idea out until needed |
| Teaching or office hours | The team has a useful point of view | Do not disguise a sales pitch as education |
| Landing-page replies | People opted into the topic | Follow up personally, not only with metrics |
| Advisors | Industry structure is unclear | Advisors should create learning, not just status |

## Meeting Framing

When a formal ask is required, include:

1. Vision: the broad problem or better world.
2. Stage: where the team is now.
3. Weakness: what the team does not understand yet.
4. Pedestal: why this person can help.
5. Ask: the specific, easy-to-forward conversation request.

Keep the framing short. Do not ask for opinions on the idea. Ask for help
understanding a domain, problem, workflow, or decision process. Prefer a short,
specific conversation over a broad "pick your brain" request.

## Output Format

```markdown
# Customer Conversation Access Plan

## Segment
[Who we need to talk to.]

## Best Access Paths
| Path | Why It Fits | First Action | Risk |
|------|-------------|--------------|------|

## Warm Intro Or Meeting Ask
- Vision:
- Stage:
- Weakness:
- Why them:
- Ask:

## Follow-Up
- Target number of conversations:
- Next source if this fails:
- What to track:
```

## Workflow

Use `workflows/frame-warm-intro.md` when drafting an intro request, meeting
request, or conversation opener.

## Quality Bar

- Do not default to cold outreach if a warmer path is plausible.
- Do not hide a sales pitch inside a request for advice.
- Do not ask for a formal meeting when a casual conversation would learn enough.
- Do not measure access only by response rate. The goal is useful
  conversations with the right people.
