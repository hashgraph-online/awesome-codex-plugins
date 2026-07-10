---
name: client-proposal
description: "Draft agency proposals. Use when: pitch deck, scope of work, SLA, capabilities presentation for prospects or clients."
---

# /digital-marketing-pro:client-proposal

## Purpose

Generate a professional marketing agency proposal or pitch document for a prospective client. Covers strategic analysis, service scope, deliverables, pricing, and team positioning to win new business or formalize an existing engagement with a polished, ready-to-customize document.

## Input Required

The user must provide (or will be prompted for):

- **Client business name and industry**: Who the proposal is for and their vertical/market segment
- **Services requested**: Which marketing services are in scope (SEO, PPC, social, content, email, strategy, creative, analytics, etc.)
- **Estimated budget range**: Client's stated or expected budget for marketing services (monthly or annual)
- **Timeline**: Engagement duration — 3-month pilot, 6-month contract, 12-month retainer, or project-based with defined milestones
- **Key challenges/goals**: What the client is trying to achieve, problems they need solved, or opportunities they want to capture
- **Competitive context**: Key competitors, market pressures, or differentiation challenges the client faces
- **Decision criteria**: What matters most to the client — price, expertise, speed, industry experience, team size, or technology
- **Proposal format**: Full written proposal, pitch deck outline, or scope-of-work document
- **Existing relationship**: New prospect, referral, existing client expansion, or RFP response
- **Internal team available**: Agency team members who would staff the account (for team bio section)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. The loaded brand should be the **agency brand** — the proposal will be written from the agency's perspective. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Research client industry benchmarks**: Pull relevant industry performance data, typical marketing spend ratios, competitive landscape patterns, and common pain points for the client's vertical
3. **Define proposed scope of services**: Map requested services to specific deliverables, ownership (agency vs. client), frequency, and dependencies between service lines
4. **Build deliverables matrix with timelines**: Create a detailed breakdown of every deliverable, its cadence (weekly, monthly, quarterly), responsible party, and approval workflow
5. **Create KPI framework with realistic targets**: Set measurable goals for each service line — baseline assumptions, 90-day targets, 6-month targets, and stretch goals tied to business outcomes
6. **Design pricing structure**: Develop 2-3 pricing options — retainer-based, project-based, or performance-based models with clear scope boundaries, overage terms, and upgrade paths
7. **Include case study references**: Frame placeholders for relevant case studies or past results that demonstrate capability in the client's industry, service area, or challenge type
8. **Draft executive summary**: Write a compelling 1-page overview that connects the client's specific challenges to the proposed solution and expected outcomes
9. **Build team and process overview**: Outline the account team structure, communication cadence (weekly calls, monthly reports, quarterly reviews), reporting rhythm, and escalation process
10. **Include terms and conditions framework**: Draft standard engagement terms covering scope change process, payment terms, IP ownership, confidentiality, data handling, performance guarantees, and termination clauses
11. **Add competitive differentiation**: Articulate why the agency is the right choice based on the client's stated decision criteria — without naming competitors directly

## Output

A structured client proposal document containing:

- **Executive summary**: Client challenges, proposed approach, and expected outcomes in a compelling 1-page overview
- **Situation analysis**: Client's current state, competitive landscape, market opportunity, and key assumptions
- **Proposed strategy**: High-level strategic approach connecting services to business goals with a clear theory of change
- **Scope of services**: Detailed service descriptions with deliverables, frequency, ownership matrix, and exclusions
- **Deliverables timeline**: Month-by-month or phase-by-phase deliverable schedule with milestones and review gates
- **KPI targets**: Measurable success metrics per service line with baseline, target, and stretch goals
- **Pricing options**: 2-3 pricing tiers or models with clear scope definitions, add-on options, and payment schedule
- **Team bios section**: Account team structure with role descriptions and placeholder bios to be filled with actual team members
- **Case study framework**: Structured placeholders for 2-3 relevant past engagements showing challenge, approach, and results
- **Terms outline**: Standard engagement terms covering scope, payment, IP, confidentiality, data, and termination
- **Next steps**: Clear action items with dates for moving from proposal to signed engagement
- **Investment justification**: ROI framework showing how the proposed services connect to measurable business outcomes
- **Risk and assumptions**: Key assumptions underpinning projections and risks that could affect delivery or results

## Agents Used

- **marketing-strategist** — Strategic positioning, service scoping, KPI framework, competitive analysis, proposal narrative, industry benchmarking
