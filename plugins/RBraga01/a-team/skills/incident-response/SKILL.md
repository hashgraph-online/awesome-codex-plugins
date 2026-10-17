---
name: incident-response
description: Production incident playbook. Use immediately when production is degraded or down. Five phases: detect, contain, diagnose, resolve, post-mortem. Prevents the chaos of uncoordinated response and ensures every incident produces lasting improvements.
---

# Incident Response

## The Law

```
CALM IS A SKILL. PANIC IS A CHOICE.
An incident is a system behaving unexpectedly. It is solved by evidence, not speed.
Fast wrong fixes extend incidents. Slow correct fixes end them.
```

## When to Use

Use this skill immediately when:
- Error rate spikes above baseline
- Latency exceeds SLA
- A service is unreachable
- Data is inconsistent or missing
- A security event is suspected

## The Five Phases

---

### Phase 1: Detect & Declare (first 5 minutes)

**Assess impact — answer three questions:**
1. What is broken? (which service, endpoint, feature)
2. Who is affected? (all users, subset, specific region, specific plan tier)
3. When did it start? (exact time from monitoring, not "someone noticed")

**Declare the incident:**
- Create an incident channel: `#incident-YYYY-MM-DD-short-description`
- Post the initial status: service, impact, start time, who is investigating
- Set the incident severity:

| Severity | Definition |
|----------|-----------|
| SEV-1 | Complete service outage or data loss. All hands. |
| SEV-2 | Critical feature broken, significant user impact. Team leads involved. |
| SEV-3 | Partial degradation, workaround exists. Engineering only. |
| SEV-4 | Minor issue, low user impact. Standard ticket. |

**Do not investigate alone for SEV-1/SEV-2.** Assign roles:
- **Incident Commander** — coordinates response, owns communication
- **Technical Lead** — drives diagnosis and fix
- **Comms** — updates status page and stakeholders

---

### Phase 2: Contain (first 15 minutes)

**Stop the bleeding before diagnosing the wound.**

Look for the fastest way to reduce impact — in this order:

1. **Rollback** — was there a recent deploy? Roll it back. Rollback is always faster than a hotfix.
   ```bash
   git revert HEAD --no-edit && git push
   # or
   kubectl rollout undo deployment/api
   ```

2. **Feature flag off** — can the broken feature be disabled without affecting the whole service?

3. **Circuit breaker / rate limit** — if a downstream service is causing the issue, can you stop calling it temporarily?

4. **Scale up** — if it's a load issue, can you add capacity immediately?

5. **Redirect traffic** — failover to a secondary region or static error page

**Containment does not require knowing the root cause.** Act fast to reduce impact, then diagnose.

---

### Phase 3: Diagnose (parallel with or after containment)

Work from evidence. No guessing.

**Evidence sources in order of reliability:**
1. Monitoring dashboards — what changed at the incident start time?
2. Error logs — what errors appear that didn't before?
3. Recent deploys — what changed in the last 24 hours?
4. Recent config changes — feature flags, environment variables, infrastructure changes
5. External dependencies — is a third-party service degraded? Check their status page.

**Diagnostic commands:**
```bash
# Recent deploys
git log --oneline -20

# Error spike in logs
grep ERROR app.log | grep "$(date +%Y-%m-%dT%H)" | wc -l

# Slow queries
psql -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Service health
kubectl get pods --all-namespaces | grep -v Running
kubectl describe pod <failing-pod>
kubectl logs <failing-pod> --previous
```

**Form a single hypothesis:** "The incident is caused by X because evidence Y shows Z."
Test it minimally before acting on it.

---

### Phase 4: Resolve

Apply the fix with the minimum blast radius.

**Fix principles:**
- Prefer rollback over hotfix — hotfixes under pressure introduce new bugs
- Apply to staging first if a <5 minute delay is acceptable
- Have a rollback plan for the fix itself
- One change at a time — never apply multiple fixes simultaneously

**After applying fix:**
- Verify the metric that triggered the incident is recovering
- Confirm no new errors introduced
- Keep monitoring for 15 minutes before declaring resolved

**Declare resolved:**
```
RESOLVED — [time]
Service restored. Root cause: [one sentence].
Follow-up actions tracked in post-mortem.
```

---

### Phase 5: Post-Mortem (within 48 hours)

Every SEV-1 and SEV-2 gets a written post-mortem. Every SEV-3 gets at least a brief one.

**Template: `docs/postmortems/YYYY-MM-DD-short-title.md`**

```markdown
# Post-Mortem: [Title]

**Date:** YYYY-MM-DD
**Severity:** SEV-N
**Duration:** Xh Ym (detected HH:MM → resolved HH:MM)
**Impact:** [who was affected and how]

## Timeline

| Time | Event |
|------|-------|
| HH:MM | First alert triggered |
| HH:MM | Engineer notified |
| HH:MM | Incident declared |
| HH:MM | Containment applied |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Incident resolved |

## Root Cause

[One clear sentence. Not "the server crashed" — why did the server crash.]

## Contributing Factors

- [What made this possible / what made detection slow / what made recovery slow]

## What Went Well

- [Things that helped, even small ones]

## Action Items

| Action | Owner | Due |
|--------|-------|-----|
| Add alert for X | @person | YYYY-MM-DD |
| Fix root cause Y | @person | YYYY-MM-DD |
| Add runbook for Z | @person | YYYY-MM-DD |
```

**Post-mortem rules:**
- Blameless — systems fail, not people
- Focus on systemic improvements, not individual mistakes
- Every action item has an owner and a date
- Action items are tracked as real tickets, not just documented and forgotten

## Communication Templates

**Status page update (during incident):**
```
[INVESTIGATING] We are investigating reports of [issue] affecting [scope].
Our team is actively working on a resolution. Next update in 30 minutes.
```

**Resolution notice:**
```
[RESOLVED] The issue affecting [scope] has been resolved as of [time].
Root cause was [brief explanation]. A full post-mortem will be published within 48 hours.
We apologise for the inconvenience.
```
