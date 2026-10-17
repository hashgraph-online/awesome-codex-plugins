# Test Case: Legitimate out-of-scope unit does not create a false positive

## Invocation

- profile: `security-audit`
- caller: `river-review-security-audit`
- mode: `focused`
- frozen scope: `src/auth/**`
- schema validation: pass
- semantic validation: pass

## Reconnaissance evidence

The payment webhook subsystem is outside the explicitly frozen `src/auth/**` audit boundary and no payment source is included in the focused audit.

## SecurityAuditCoverage

```json
{
  "kind": "SecurityAuditCoverage",
  "schemaVersion": "1",
  "taxonomyVersion": "0.1.0",
  "executionPolicy": "source-only",
  "totalUnits": 1,
  "applicableUnits": 0,
  "coveredUnits": 0,
  "plannedUnits": 0,
  "blockedUnits": 0,
  "deferredUnits": 0,
  "outOfScopeUnits": 1,
  "openUnitIds": [],
  "units": [
    {
      "id": "payment-webhook",
      "subsystem": "payments",
      "trustBoundary": "payment-provider-to-webhook-handler",
      "attackClassId": "rpc-messaging",
      "state": "out_of_scope",
      "reasonCode": "scope_excluded",
      "reviewedPaths": [],
      "evidenceRefs": [],
      "relatedFindingIds": [],
      "validationPlan": null,
      "explanation": "Focused audit scope is src/auth/**; the payment webhook subsystem is explicitly outside that frozen boundary."
    }
  ]
}
```

## Expected Behavior

- Do not report a coverage gap merely because the unit is `out_of_scope`.
- Accept the exclusion as credible because it matches the frozen focused scope and reconnaissance evidence.
- Do not count the exclusion as proof of security coverage or safety.
