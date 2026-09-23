---
name: best-practices
description: "Research current practices or compare approaches using primary evidence and the user's constraints."
argument-hint: "<topic>"
user-invocable: true
allowed-tools: WebSearch, WebFetch, Read, Glob, Grep, Skill
---

# Best practices

Research the requested topic with current, high-quality evidence and first-principles reasoning.
Keep research artifacts outside the repository unless the result remains useful after the task.
If a subagent performs the research, give the main agent the artifact paths.

For technical topics, prefer primary and authoritative sources:

- official documentation and specifications;
- maintainer posts, authoritative engineering blogs, and peer-reviewed papers;
- widely adopted open-source projects that are actively maintained.

Age each claim against its own horizon.
Versions, APIs, pricing, limits, and advisories can change within weeks.
Tool choices can change within months. Architecture and patterns can remain valid for years.
Explain why an older source still applies and check whether a newer source replaced it.
Mark facts that you cannot confirm as unverified.

Cite material claims inline and separate evidence from inference.
Explain consensus, disagreement, uncertainty, and where each recommendation applies.
State what evidence would overturn the recommendation.
Recommend for the user's goals and constraints, not for an imaginary average user.

If missing context changes the answer, ask for it or give clearly conditional recommendations.
Do not pad the report with source quotas, evidence labels, or weak secondary sources.
