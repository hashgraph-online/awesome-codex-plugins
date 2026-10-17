---
name: clueless-help
description: "Use when the user asks how clueless works, what its commands or levels are, or types /clueless-help."
license: MIT
metadata:
  tags: "command-reference, reviewability, agent-skills"
  languages: "en"
---

Answer with this table and nothing else.

| Command | What it does |
|---------|--------------|
| `/clueless [lite \| full \| ultra \| off]` | Set how much responsibility the agent takes. No argument: report the current level. |
| `/clueless-blindspots` | One-shot: what you are not seeing in the plan, code, or document in front of you. |
| `/clueless-help` | This table. |

Levels: **lite** adds only the "decided for you / only you can decide" handoff.
**full** (default) delivers in the full contract: do this, careful, check it
worked, decided for you, only you can decide. **ultra** also challenges whether
the task as stated is the task you need.

Off: "stop clueless" or "normal mode".
