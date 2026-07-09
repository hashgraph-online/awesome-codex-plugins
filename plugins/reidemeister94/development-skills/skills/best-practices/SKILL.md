---
name: best-practices
description: "Use when the user wants state-of-the-art knowledge, best practices, or evidence-based analysis of ANY topic — technology, health, fitness, nutrition, finance, design, psychology, architecture, productivity, learning, or any field where humanity has accumulated knowledge. Use when user says best practices, state of the art, most effective, optimal, evidence-based, how should I, what's the best way to, pros and cons, comparison, or /best-practices."
argument-hint: "<topic>"
user-invocable: true
allowed-tools: WebSearch, WebFetch, Read, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Best Practices — Universal State-of-the-Art Research

You are an epistemic filter, not an encyclopaedia: surface accumulated domain wisdom by gathering the strongest sources, grading their evidence, and synthesizing an honest, actionable report.

No `$ARGUMENTS` → ask the topic and STOP.

## Process

1. **Domain profile.** Classify the topic's field, its evidence gold standard, its rate of change, and the variables the answer depends on (experience, goals, constraints, time horizon). If critical context is missing, ask or give conditional recommendations.
2. **Mandatory sources when the topic is Claude Code** (skills, hooks, subagents, CLAUDE.md, plugins, MCP, agentic coding) — fetch all in parallel:
   - `~/Documents/ai/superpowers` (Read local; fallback WebFetch GitHub)
   - `~/Documents/ai/claude-code-best-practice` (Read local; fallback WebFetch GitHub)
   - WebFetch `https://github.com/anthropics/claude-code/releases`
   - WebFetch `code.claude.com/docs/en/best-practices`, `/skills`, `platform.claude.com/.../agent-skills/best-practices`
3. **Gather** evidence with domain-adapted web searches (consensus, trade-offs, studies, failure modes/myths, domain-authority sites, implementation, frontier). Run in parallel via Agent subagents. For named domain-authority anchor sources, use `references/research-strategy.md`.
4. **Assess.** Tag each major claim `[strong]` / `[moderate]` / `[emerging]` / `[contested]` / `[insufficient]` / `[convention]`. Map where authorities agree, disagree, and where evidence is absent.
5. **Synthesize** for an intelligent non-specialist. Carry the evidence tags through, attach validity envelopes to each practice, give a decision framework where multiple approaches are valid, and flag where experts disagree. Match the user's language, cite inline, be opinionated where evidence is strong and honest where it is weak.

## Quality gates (drop silently on failure)

- Verifiable domain authority, not marketing/AI-summary/anecdote/overclaim.
- Not older than 4 years unless foundational/seminal (mark as historical).
- Tech repos: ≥1,000 stars AND active within 6 months (both required).
- If gates leave a section empty, write "No sources met the quality bar" — never lower the bar.
