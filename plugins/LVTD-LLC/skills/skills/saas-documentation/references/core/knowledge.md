# SaaS Documentation Knowledge

SaaS documentation explains a living service: what changed, what the provider manages, what the customer controls, and how internal teams keep the service dependable.

Source basis: *The Product Is Docs*, Chapter 25, "Writing SaaS Documentation," Chapter 10, "Maintaining Existing Content," Chapter 18, "Working with Customer Support," and Chapter 2, "Agile."

## Key Concepts

### Managed-Service Boundary

**Definition**: The line between provider-managed service responsibilities and customer-controlled configuration, data, identity, integrations, or usage.

SaaS docs should not assume readers know who owns backups, upgrades, access, retention, browser support, incident action, or integration behavior.

### Fleet-Wide Impact

**Definition**: A change that can affect many customers at once because they share a hosted service or release channel.

Fleet-wide changes need release notes, support readiness, monitoring, and sometimes customer communication before public docs alone are sufficient.

### Customer-Controlled Configuration

**Definition**: Settings, permissions, workflows, data, or integrations that customers must configure or govern.

Docs should explain prerequisites, roles, defaults, limits, and consequences of misconfiguration.

### Internal Service Docs

**Definition**: Runbooks, escalation paths, incident notes, release enablement, and support procedures that help teams operate the SaaS product.

Internal docs can shape the customer experience as much as public docs because they affect support speed, incident handling, and upgrade consistency.

## Responsibility Matrix

| Area | Provider Typically Manages | Customer Typically Controls |
|------|----------------------------|-----------------------------|
| Upgrades | Deployment, compatibility, rollout, rollback | Change awareness, testing affected workflows |
| Access | Platform roles, authentication features, audit logs | User assignment, IdP setup, least privilege |
| Data | Service availability, retention mechanics, backups when offered | Data entry, export, retention choices, deletion decisions |
| Integrations | API behavior, webhooks, platform limits | Secrets, endpoints, retry handling, downstream systems |
| Incidents | Detection, mitigation, status updates | Customer-side validation, escalation, business continuity |
| Browser or UI support | Supported browsers, UI changes, accessibility fixes | Client environment, user training, local policy |

## Core Rules

1. **State the service model** - Make clear whether the product is provider-managed, customer-managed, or shared.
2. **Document customer action** - Release docs should say who is affected and what they must do.
3. **Separate public and internal needs** - Customers need tasks and impact; support and operations need runbooks, escalation, and verification.
4. **Name permissions and prerequisites** - SaaS tasks often depend on plan, role, region, browser, tenant state, feature flag, or integration access.
5. **Explain defaults and limits** - Hidden defaults create support load and risky assumptions.
6. **Treat UI labels as volatile** - Verify screenshots, labels, and paths near release.
7. **Plan for frequent change** - Use owners, review triggers, and dependency audits for settings, screenshots, examples, and release notes.
8. **Write for incident recovery** - Runbooks need exact signals, severity, customer impact, and rollback or mitigation steps.
9. **Keep support in the loop** - Support patterns reveal missing docs, confusing flows, and customer language.
10. **Avoid false universality** - Hosted products may vary by plan, region, rollout, entitlement, or migration cohort.
11. **Validate internal docs like product docs** - Runbooks and enablement need testing, owners, and freshness triggers.
12. **Escalate service complexity** - If docs require many exceptions, surface product, UX, or operations complexity.

## SaaS Doc Types

| Need | Recommended Doc |
|------|-----------------|
| User must configure something | Admin how-to or setup guide |
| User must understand provider/customer responsibilities | Concept or responsibility page |
| User must act because behavior changed | Release note plus affected task updates |
| Support must handle repeatable issue | Support runbook |
| Operations must restore or mitigate service state | Operations runbook |
| Many teams need launch readiness | Release enablement note |
| Customers need status during incident | Status update or incident communication |

## Common Misconceptions

- **Myth**: SaaS docs are simpler because customers do not install software.
  **Reality**: SaaS reduces some setup work but adds responsibility boundaries, fleet-wide change, operations, and support readiness.
- **Myth**: Internal runbooks are not documentation quality work.
  **Reality**: Runbooks affect customer trust through incident response, upgrades, and support consistency.
- **Myth**: Release notes only need to list new features.
  **Reality**: SaaS release notes should explain impact, action, timing, permissions, limits, and support paths.
- **Myth**: One current-version doc is always enough.
  **Reality**: Rollouts, migrations, plan differences, and region availability can create temporary or lasting variants.

## Red Flags

- No one can explain what the provider manages versus what the customer controls.
- Release notes say "improved" or "updated" without customer impact.
- A public task depends on an internal runbook that has no owner or review trigger.
- UI screenshots are stale or release timing is uncertain.
- Support has a workaround that public docs do not mention or explain.
- Permission, browser, plan, region, or feature-flag requirements are missing.
- Incident procedures omit customer impact and verification.

## Patterns

### SaaS Topic Pattern

```text
Title: Configure SAML single sign-on for a workspace
Audience: Workspace admin with identity-provider access
Provider manages: SSO settings UI, ACS URL, metadata endpoint, audit events
Customer controls: IdP configuration, user assignment, certificate rotation
Prerequisites: Enterprise plan, admin role, supported IdP, verified domain
Procedure: Configure IdP -> upload metadata -> test login -> enforce policy
Verification: Test user can sign in and audit event appears
Support path: Link troubleshooting and rollback steps
```

### SaaS Release Note Pattern

```text
Change: Notification delivery retries now stop after 72 hours
Affected customers: Workspaces using webhook notifications
Customer action: Review endpoint reliability and alerting before July 15
Provider action: New retry policy rolls out automatically
Docs affected: Webhooks overview, retries reference, troubleshooting
Support readiness: Support runbook updated with replay procedure
```

### Runbook Pattern

```text
Runbook: Replay failed webhook deliveries for a workspace
Trigger: Customer reports missing notifications and delivery logs show retry exhaustion
Customer impact: Downstream system may be missing events
Prerequisites: Incident role, workspace ID, delivery ID, customer approval if required
Steps: Confirm scope -> replay delivery -> verify success -> update incident notes
Review trigger: Delivery service change, retention change, incident postmortem
```
