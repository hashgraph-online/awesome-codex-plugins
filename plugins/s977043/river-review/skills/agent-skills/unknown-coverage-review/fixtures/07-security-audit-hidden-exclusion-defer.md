# Test Case: Broad exclusion and defer remain visible as residual coverage risk

## Invocation

- profile: `security-audit`
- caller: `river-review-security-audit`
- mode: `full-audit`
- schema validation: pass
- semantic validation: pass

## Reconnaissance evidence

The repository contains a multi-tenant API and an AI tool executor. Both are inside the repository-wide frozen scope.

## SecurityAuditCoverage

```json
{
  "kind": "SecurityAuditCoverage",
  "schemaVersion": "1",
  "taxonomyVersion": "0.1.0",
  "executionPolicy": "source-only",
  "totalUnits": 3,
  "applicableUnits": 1,
  "coveredUnits": 0,
  "plannedUnits": 0,
  "blockedUnits": 0,
  "deferredUnits": 1,
  "outOfScopeUnits": 2,
  "openUnitIds": ["agent-tools"],
  "units": [
    {
      "id": "tenant-authz",
      "subsystem": "api",
      "trustBoundary": "tenant-api-to-data-store",
      "attackClassId": "tenant-isolation",
      "state": "out_of_scope",
      "reasonCode": "scope_excluded",
      "reviewedPaths": [],
      "evidenceRefs": [],
      "relatedFindingIds": [],
      "validationPlan": null,
      "explanation": "Not reviewed in this run."
    },
    {
      "id": "api-authz",
      "subsystem": "api",
      "trustBoundary": "client-to-api",
      "attackClassId": "authn-authz",
      "state": "out_of_scope",
      "reasonCode": "scope_excluded",
      "reviewedPaths": [],
      "evidenceRefs": [],
      "relatedFindingIds": [],
      "validationPlan": null,
      "explanation": "Not reviewed in this run."
    },
    {
      "id": "agent-tools",
      "subsystem": "agent-runtime",
      "trustBoundary": "model-to-tool-executor",
      "attackClassId": "ai-agent-security",
      "state": "deferred",
      "reasonCode": "budget_deferred",
      "reviewedPaths": ["src/agent/tools.mjs"],
      "evidenceRefs": [],
      "relatedFindingIds": [],
      "validationPlan": "Inspect capability scoping and authorization before the next full-audit report is treated as current.",
      "explanation": "Audit budget ended before tool capability paths were traced."
    }
  ]
}
```

## Expected Behavior

- Surface the two broad `scope_excluded` entries as suspicious because they conflict with repository-wide scope and reconnaissance evidence.
- Keep the deferred AI-agent unit visible with its validation plan.
- Do not convert these coverage states directly into vulnerability findings or deterministic Gate decisions.
