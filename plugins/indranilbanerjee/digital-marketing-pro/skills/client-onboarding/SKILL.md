---
name: client-onboarding
description: "Plan client onboarding. Use when: kickoff agenda, discovery questionnaire, account setup checklist, 30-60-90 day plan."
---

# /digital-marketing-pro:client-onboarding

## Purpose

Generate a comprehensive client onboarding workflow for a new marketing engagement. Covers kickoff planning, discovery, stakeholder alignment, access provisioning, milestone setting, and communication protocols to ensure a smooth transition from signed contract to active account with clear expectations on both sides.

## Input Required

The user must provide (or will be prompted for):

- **Client name and industry**: The new client's business name, vertical, and market segment
- **Services contracted**: Which marketing services are included in the engagement (SEO, PPC, social, content, email, analytics, etc.)
- **Engagement timeline**: Contract duration and key dates — start date, first deliverable, first review, contract end
- **Team structure (agency side)**: Account lead, strategist, specialists, and any shared resources assigned to the account
- **Team structure (client side)**: Primary contact, marketing lead, approvers, and subject matter experts available
- **Account access needs**: Platforms, tools, and accounts requiring credentials or permissions (Google Ads, Analytics, CMS, social accounts, CRM, etc.)
- **Client maturity level**: Startup, SMB, or enterprise — determines complexity of onboarding, approval layers, and compliance requirements
- **Stakeholder list**: All individuals involved in the engagement with roles, decision authority, and communication preferences
- **Communication preferences**: Preferred channels (Slack, email, calls), timezone, meeting availability, and response time expectations
- **Success criteria**: What the client considers a successful engagement at 30, 60, and 90 days — and contractual KPIs if defined

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Research client industry onboarding best practices**: Identify industry-specific onboarding considerations — regulatory requirements, seasonal timing, common data sources, and typical ramp-up periods for the client's vertical
3. **Build kickoff meeting agenda**: Structure a 60-90 minute kickoff covering introductions, engagement overview, goals alignment, process walkthrough, access handoff, communication setup, and immediate next steps
4. **Create discovery questionnaire**: Draft 20-30 questions covering business context, competitive landscape, past marketing efforts, brand guidelines, content assets, data access, approval workflows, and success definitions
5. **Map stakeholders and decision-makers**: Build a stakeholder map with RACI matrix (Responsible, Accountable, Consulted, Informed) for key activities — content approval, budget changes, strategy shifts, reporting, and escalations
6. **Define access and permissions checklist**: Create a platform-by-platform checklist of all accounts, tools, and systems needing access — with permission level, owner, and deadline for provisioning
7. **Set 30-60-90 day milestones**: Define specific, measurable milestones for each phase — discovery and setup (30 days), optimization and early results (60 days), full operation and first performance review (90 days)
8. **Establish communication cadence**: Design the recurring meeting and reporting schedule — weekly status calls, monthly performance reports, quarterly business reviews, and ad-hoc escalation triggers
9. **Create escalation protocol**: Define severity tiers (informational, urgent, critical), response time expectations, escalation paths on both agency and client sides, and resolution tracking
10. **Build knowledge transfer checklist**: List all assets, documents, logins, brand files, historical data, and institutional knowledge the client needs to provide for the agency to operate effectively
11. **Compile into unified onboarding document**: Assemble all components into a single structured onboarding package with clear ownership, deadlines, and a first-week action plan for immediate momentum

## Output

A structured client onboarding package containing:

- **Kickoff meeting agenda**: 60-90 minute structured agenda with discussion topics, time allocations, presenters, and pre-read materials
- **Discovery questionnaire**: 20-30 targeted questions organized by category (business, competitive, brand, technical, process) with space for responses
- **Stakeholder map with RACI matrix**: Visual map of all stakeholders with decision authority, RACI assignments for key activities, and contact details
- **Account access checklist**: Platform-by-platform list with required permission levels, current owner, agency contact, and provisioning deadline
- **30-60-90 day milestone plan**: Phase-based milestone schedule with specific deliverables, success criteria, and checkpoint dates per phase
- **Communication cadence**: Complete meeting and reporting schedule — weekly, monthly, and quarterly touchpoints with attendees and agenda templates
- **Escalation protocol**: Severity tier definitions (informational/urgent/critical) with response times, escalation paths, and resolution tracking process
- **Knowledge transfer checklist**: Categorized list of all assets, documents, data, and access the client must provide with deadlines and responsible parties
- **Welcome email template**: Ready-to-send email introducing the account team, confirming kickoff details, and listing pre-kickoff action items
- **Internal team brief**: Agency-internal document summarizing client context, key stakeholders, sensitivities, opportunities, and account strategy
- **Risk register with mitigation**: Identified onboarding risks (delayed access, stakeholder availability, data gaps) with likelihood, impact, and mitigation steps
- **First-week action plan**: Day-by-day schedule for the first five business days with specific tasks, owners, and completion criteria

## Agents Used

- **marketing-strategist** — Stakeholder mapping, milestone planning, communication design, discovery questionnaire development, risk assessment, and onboarding workflow orchestration
