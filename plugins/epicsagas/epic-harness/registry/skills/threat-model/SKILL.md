---
name: threat-model
description: "Threat modeling and attack surface analysis. Use when assessing security boundaries, modeling threat actors, or generating threat scenarios."
---

# Threat Model — Attack Surface Analysis

## Iron Law

Every system has an attack surface. If you haven't identified it, you haven't secured it.

## Process

### Step 0: Load Engagement Context

Check for `.harness/engagement.md` in the project root. If present, load the scope (in-scope/out-of-scope) and constraints. Skip threat modeling for explicitly out-of-scope components.

Without engagement context, proceed with full-surface analysis.

### Step 1: Identify Trust Boundaries

Map every boundary where data crosses a trust level:

1. **External → Internal**: API endpoints, webhooks, file uploads, user input
2. **Internal → Privileged**: DB queries, file system access, shell execution
3. **Service → Service**: Inter-service communication, message queues, shared state
4. **Client → Server**: Auth tokens, session state, CORS origins

For each boundary, document:
- Data flow direction
- Input validation present (yes/no/partial)
- Authentication required (yes/no)
- Encryption in transit (yes/no)

### Step 2: Enumerate Threat Actors

| Actor | Motivation | Capability | Target |
|-------|-----------|------------|--------|
| Anonymous user | Exploration | Low | Public endpoints |
| Authenticated user | Data access | Medium | Own data + IDOR targets |
| Malicious insider | Data exfiltration | High | All internal systems |
| Compromised dependency | Supply chain | Variable | Build/deploy pipeline |

### Step 3: Generate Threat Scenarios

For each trust boundary × threat actor combination, generate:

1. **Attack vector**: How the boundary is crossed maliciously
2. **Impact**: What is compromised (CIA triad — Confidentiality, Integrity, Availability)
3. **Likelihood**: High/Medium/Low based on exposure and complexity
4. **Existing mitigations**: What already prevents this
5. **Gap**: What is missing

### Step 4: Produce Output

Write `THREAT_MODEL.md`:

```markdown
# Threat Model — {project}

## Scope
- In-scope: {from engagement.md or full codebase}
- Out-of-scope: {from engagement.md or none}
- Date: {ISO date}

## Trust Boundaries
| # | Boundary | Direction | Validation | Auth | Encryption |
|---|----------|-----------|------------|------|------------|
| 1 | ... | ... | ... | ... | ... |

## Threat Scenarios
| ID | Boundary | Actor | Vector | Impact | Likelihood | Mitigated | Gap |
|----|----------|-------|--------|--------|------------|-----------|-----|
| T1 | ... | ... | ... | ... | ... | Partial | ... |

## Priority Remediation
1. [CRITICAL] {highest risk gap}
2. [HIGH] {next gap}
3. [MEDIUM] {remaining gaps}

## Assumptions
- {list all assumptions made during analysis}
```

### Step 5: Feed into vuln-scan

After producing the threat model, suggest:
**"Run `/vuln-scan` to validate threat scenarios against the codebase."**

## Anti-Rationalization

| Excuse | Rebuttal | What to do instead |
|--------|----------|-------------------|
| "We don't have any external-facing components" | Internal trust boundaries are attack surfaces too. Lateral movement starts inside. | Model internal boundaries with the same rigor. |
| "Threat modeling is overkill for a small project" | Small projects get breached too. The model is proportional to the codebase. | Run the process. It takes 10 minutes. A breach takes months. |
| "We already have a threat model" | Threat models expire. Every code change can invalidate assumptions. | Update the model when significant changes land. |
| "The framework handles security" | Frameworks don't model YOUR business logic threats. | Add application-layer threat scenarios on top of framework defaults. |

## Evidence Required

- [ ] Every trust boundary in the codebase identified
- [ ] At least 2 threat scenarios per boundary
- [ ] Each scenario has impact, likelihood, and gap assessment
- [ ] Priority remediation list ordered by risk
- [ ] Assumptions explicitly listed (not hidden)

## Red Flags

- Skipping boundaries because they're "internal"
- Listing only one threat scenario per boundary
- Marking all scenarios as "already mitigated" without evidence
- No assumptions section — means assumptions are hidden, not absent
- Threat model that doesn't reference actual code paths
