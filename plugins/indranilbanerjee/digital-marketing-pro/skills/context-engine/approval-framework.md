# Approval Framework — Risk Classification & Approval Rules

Every marketing action executed through the Digital Marketing Pro plugin is classified by risk level. This framework determines whether an action can auto-execute or requires explicit user approval. Agents must evaluate risk before any execution step.

---

## 1. Risk Levels

Actions are classified into four risk levels. The classification determines the approval flow.

| Risk Level | Approval Required | Response Time | Description |
|---|---|---|---|
| **Low** | Auto-confirm + execute | Immediate | Read-only operations and internal-only outputs. No external audience impact, no budget spend, no data modification. |
| **Medium** | Review + explicit approve | User confirms once | External-facing content with limited blast radius. Moderate audience size, no budget commitment, reversible actions. |
| **High** | Budget/data confirmation required | User confirms with specifics (amount, count) | Actions involving money, large audiences, or bulk data changes. Requires the user to acknowledge the specific scope. |
| **Critical** | Double confirmation + compliance review | User confirms twice; compliance rules auto-checked | High-spend actions, regulated industries, large-scale sends, or irreversible operations. |

### Low Risk — Auto-Confirm

| Action | Why Low |
|---|---|
| Slack notifications and internal messages | Internal only, no external audience |
| Google Sheets exports and data dumps | Read/write to user's own workspace |
| Knowledge storage and memory operations | Internal persistence, no external impact |
| Read-only analytics queries | No data modification, no audience impact |
| Internal performance reports | Not client-facing, no external distribution |
| Brand voice scoring and content grading | Analysis only, no publishing |
| Keyword research and competitor lookups | Research only, no execution |

### Medium Risk — Review + Approve

| Action | Why Medium |
|---|---|
| Blog post publishing | External-facing but single URL, reversible (set to draft) |
| Social media post scheduling | External-facing but limited to followers, deletable |
| Email campaigns <1,000 recipients | External-facing, moderate audience, cannot recall but limited blast radius |
| CRM individual contact creation (<10 records) | Data modification but small scope, reversible |
| Audience segment creation | No direct send, but defines future targeting |
| Report delivery to external recipients | Client-facing content, cannot unsend |
| Content calendar updates | Planning artifact, no direct execution |

### High Risk — Budget/Data Confirmation

| Action | Why High |
|---|---|
| Ad campaign creation (any platform) | Budget commitment begins immediately upon activation |
| Budget changes >$100/day | Financial impact, may exceed approved spend |
| Bulk email sends (1,000-10,000 recipients) | Large audience, cannot recall, reputation risk |
| CRM bulk imports (100-1,000 records) | Data integrity risk at scale |
| SMS campaigns (any size) | Per-message cost, compliance complexity, cannot recall |
| CRM field updates affecting >10 records | Bulk data modification, potential data loss |
| Ad creative refresh on active campaigns | May disrupt performing campaigns |

### Critical Risk — Double Confirmation + Compliance

| Action | Why Critical |
|---|---|
| Ad campaigns with daily budget >$1,000 | Significant financial exposure |
| Bulk email sends >10,000 recipients | Major reputation risk, deliverability impact |
| Regulated industry campaigns (healthcare, finance, alcohol, cannabis, gambling, pharmaceuticals) | Legal liability, potential fines |
| CRM data deletion (any volume) | Irreversible data loss |
| WhatsApp marketing campaigns | Per-conversation cost, template approval required, compliance complexity |
| Actions on a new/untested platform | Unknown failure modes, no established playbook |
| Cross-border campaigns into new jurisdictions | New compliance requirements may apply |
| Campaigns targeting minors or age-restricted audiences | COPPA, GDPR Article 8, platform age-gate requirements |

---

## 2. Industry-Specific Gates

Campaigns in regulated industries require additional compliance checks before any risk level approval proceeds. These gates are mandatory and cannot be bypassed.

| Industry | Required Gate | Specific Checks |
|---|---|---|
| **Healthcare** | HIPAA review | No PHI in marketing content; no unapproved treatment claims; "consult your healthcare provider" disclaimer; fair balance for Rx products; medical claims substantiation |
| **Finance** | FINRA/SEC disclaimers | "Past performance" warning on any returns mention; APR disclosure for credit products; no guaranteed return language; fee disclosure; net-of-fee performance data |
| **Alcohol** | Age gate + TTB compliance | 21+ age verification on landing pages; no minor-appealing imagery; responsible drinking messaging; no health claims; 70%+ adult audience threshold for ad placement |
| **Cannabis** | Jurisdiction + platform check | Legal jurisdiction verification; no cross-border marketing; major ad platforms prohibit paid cannabis ads; no medical/health claims; state-specific warning language; license number disclosure |
| **Gambling** | Responsible messaging | Responsible gambling messaging in all creatives; self-exclusion links; jurisdiction-specific licensing verification; no targeting minors; problem gambling helpline number |
| **Pharmaceuticals** | FDA compliance | Fair balance requirement (risks and benefits); black box warning inclusion where required; no off-label promotion; DTC ad requirements; brief summary or adequate provision |
| **Real Estate** | Fair Housing Act | Equal Housing Opportunity statement; no discriminatory language or targeting; Special Ad Category on Meta/Google; diverse imagery; no exclusionary audience criteria |
| **Supplements** | FTC/FDA review | No disease claims; FDA structure/function disclaimer; "results not typical" for testimonials; substantiation for all efficacy claims; no "FDA approved" language |

---

## 3. Approval Flow

Every action follows this decision tree from draft to execution.

```
Draft Action
    |
    v
Compliance Check (auto)
    |-- Fail --> BLOCK: Show violation, cite specific rule, suggest fix
    |-- Pass --> continue
    |
    v
Industry Gate Check (auto, if regulated industry)
    |-- Fail --> BLOCK: Show missing compliance element
    |-- Pass --> continue
    |
    v
Risk Assessment (auto)
    |
    +-- Low Risk --------> Auto-approve --> Execute --> Verify --> Log
    |
    +-- Medium Risk -----> Present summary to user
    |                          |-- User approves --> Execute --> Verify --> Log
    |                          |-- User rejects --> Revise or cancel
    |
    +-- High Risk -------> Present summary with budget/scope details
    |                          |-- User confirms specifics --> Execute --> Verify --> Log
    |                          |-- User rejects --> Revise or cancel
    |
    +-- Critical Risk ---> Present summary + compliance report
                               |-- User confirms (1st) --> "Please confirm again: [action summary]"
                               |-- User confirms (2nd) --> Execute --> Verify --> Log
                               |-- User rejects --> Revise or cancel
```

### Confirmation Message Templates

| Risk Level | Confirmation Prompt |
|---|---|
| **Medium** | "Ready to publish [action type] to [destination]. [Brief summary]. Proceed?" |
| **High** | "This will [action] affecting [scope]. Daily budget: $[amount]. Audience size: [count]. Confirm to proceed." |
| **Critical** | "CRITICAL ACTION: [action type] in [regulated industry / high-spend context]. Budget: $[amount]/day. Audience: [count] recipients in [jurisdictions]. Compliance checks passed. Please confirm to proceed." Then: "Please confirm one more time to execute this action." |

---

## 4. Rollback Procedures

When an executed action needs to be reversed, follow these procedures immediately.

| Action Type | Rollback Procedure | Time Sensitivity | Data Recovery |
|---|---|---|---|
| **Blog post** | Set post status to "draft." Remove URL from sitemap. Request search engine re-crawl if indexed. Clear CDN cache. | Low (minutes to hours) | Full recovery |
| **Email campaign** | Cannot recall sent emails. Immediately send a correction/retraction email if content was incorrect. Update suppression lists. Document the incident. | N/A — prevention is key | No recall possible |
| **Ad campaign** | Pause campaign immediately. Review spend incurred. Document performance data before pausing. If compliance issue, also remove/archive creatives. | High (spend accumulates every minute) | Financial: partial (unspent budget returned) |
| **Social media post** | Delete post from platform. Archive content locally. If screenshot has spread, prepare a response statement. | Medium (shares propagate quickly) | Post deleted; shares persist |
| **CRM import** | Revert from pre-import backup snapshot (see CRM Operations Workflow step 4). Verify record count returns to pre-import state. Validate no orphaned records. | Medium | Full recovery from snapshot |
| **SMS/WhatsApp** | Cannot recall sent messages. If ongoing campaign, pause immediately. For incorrect content, send a follow-up correction. Update opt-out lists. | N/A — prevention is key | No recall possible |
| **Report delivery** | Send a correction notice to all recipients. Provide corrected report. Mark original as superseded. | Medium | Correction replaces original |

### Rollback Logging

Every rollback must be logged with:
- Original action ID and timestamp
- Rollback reason (compliance issue, incorrect content, user request, error)
- Rollback steps taken
- Verification that rollback completed successfully
- Incident review notes (what went wrong, how to prevent recurrence)

---

## 5. Escalation Rules

Escalate to the user immediately (do not proceed with execution) when any of the following conditions are detected.

| Trigger | Threshold | Escalation Action |
|---|---|---|
| **Budget overrun** | Actual spend exceeds planned budget by >10% | Pause campaign. Report: planned vs. actual spend, projected overage, recommended action. |
| **Compliance flag** | Any BLOCK-level compliance violation detected (see `compliance-rules.md` severity levels) | Halt execution. Report: specific rule violated, content that triggered the flag, recommended fix. |
| **Platform error** | API returns error on campaign creation or modification | Retry once after 60 seconds. If second attempt fails, report: error code, error message, platform status page link. |
| **Unexpected audience size** | Audience size differs from estimate by >50% (either direction) | Pause before send/launch. Report: expected vs. actual count, possible causes (segment definition change, list growth/decay). |
| **Negative sentiment spike** | Social listening or engagement metrics show >3x normal negative response rate within 2 hours | Alert user. Provide: negative comment samples, sentiment score, recommended response (pause campaign, prepare statement, or monitor). |
| **Deliverability drop** | Email bounce rate >5% or spam complaint rate >0.3% during a send | Pause remaining sends. Report: bounce/complaint count, affected ISPs, recommended list hygiene actions. |
| **Performance anomaly** | Any primary KPI drops >50% vs. previous period with no known cause | Alert user. Provide: metric comparison, possible causes (tracking issue, platform change, competitive action, seasonality). |
| **Data integrity issue** | CRM import validation finds >5% of records failing validation | Halt import. Report: failure count, failure reasons, sample of failed records, recommended fix. |
