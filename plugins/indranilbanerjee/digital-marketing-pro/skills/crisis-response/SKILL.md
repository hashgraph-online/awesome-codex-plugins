---
name: crisis-response
description: "Manage PR crises. Use when: reputational threat emerges, need stakeholder messaging, or communication timeline."
argument-hint: "[situation-description]"
---

# /digital-marketing-pro:crisis-response

## Purpose

Provide rapid crisis assessment and a structured response plan. Classifies severity, identifies stakeholders, drafts messaging for each audience, and builds a communication timeline to contain damage and rebuild trust.

## Input Required

The user must provide (or will be prompted for):

- **What happened**: Description of the crisis or incident
- **When it started**: Timeline of events so far
- **Current exposure**: How widely known is it (internal only, social media, press coverage)
- **Stakeholders affected**: Customers, employees, investors, partners, public
- **Actions taken so far**: Any statements, fixes, or responses already issued
- **Spokesperson**: Who will speak for the brand

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Severity classification**: Level 1 (monitor), Level 2 (respond), Level 3 (full mobilization) based on reach, impact, and trajectory
3. Assess the narrative: What is being said? What is the public sentiment? What is the worst-case escalation?
4. Identify all stakeholder groups and prioritize communication order
5. Draft holding statement for immediate release (within first hour)
6. Draft tailored messaging per stakeholder: customers, employees, media, partners, social media
7. Build communication timeline: first hour, first 24 hours, first week, ongoing
8. Define channel strategy: which messages go where (social, email, press, internal comms)
9. Outline recovery plan: corrective actions, transparency updates, trust-rebuilding initiatives
10. Set monitoring cadence and escalation triggers

## Output

A structured crisis response plan containing:

- Severity classification with rationale
- Situation assessment and narrative analysis
- Holding statement (ready to publish)
- Stakeholder-specific messaging (customers, media, employees, partners)
- Communication timeline with milestones and decision points
- Channel deployment plan
- Social media response guidelines (what to reply, what to ignore, when to escalate)
- Recovery and trust-rebuilding roadmap
- Monitoring plan with escalation triggers

## Agents Used

- **brand-guardian** — Brand protection, messaging consistency, stakeholder communication, compliance
- **pr-outreach** — Media relations, press statement, journalist engagement strategy
