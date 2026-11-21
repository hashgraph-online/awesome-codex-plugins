---
name: best-practices
description: "Use when current practice or outside evidence can change a decision: comparing approaches, libraries, or patterns against the user's constraints."
argument-hint: "<topic>"
user-invocable: true
allowed-tools: WebSearch, WebFetch, Read, Glob, Grep, Skill
---

Given a topic, you have to search online for the best, high quality, updated information about it, using critical thinking and reasoning by first principles.
Save your searches result to a temporary file on the user system and if you are a subagent,
tell to the main agent the path of those files so he can read them in detail.

On technical topics, take evidence only from top sources, not SEO stuff or AI slop:

- official documentations and specifications
- maintainer posts, authoritative engineering blogs, peer-reviewed papers
- widely adopted github projects that are still actively maintained (ideally > 2k stars and last commit < 3 weeks ago)

Age each claim against its own horizon: weeks for versions, APIs, pricing, limits, and advisories; months for tool and library choices; years for architecture, patterns, and concepts. An old source holds when the idea still holds. Say why it holds, and confirm that no newer source replaced it. Mark what you cannot confirm as unverified.

Cite material claims inline, and separate evidence from inference. Explain consensus, disagreement, uncertainty, and where each recommendation applies. State what evidence would overturn your recommendation. Recommend for the user's goals and constraints, not for an imaginary average user.

If missing context changes the answer, ask for it or give clearly conditional recommendations. Do not pad the report with source quotas, evidence labels, or weak secondary material.
