# Test Case: Shape-valid covered claim has weak semantic evidence

## Invocation

- profile: `security-audit`
- caller: `river-review-security-audit`
- schema validation: pass
- semantic validation: pass

## SecurityAuditCoverage

```json
{
  "kind": "SecurityAuditCoverage",
  "schemaVersion": "1",
  "taxonomyVersion": "0.1.0",
  "executionPolicy": "source-only",
  "totalUnits": 1,
  "applicableUnits": 1,
  "coveredUnits": 1,
  "plannedUnits": 0,
  "blockedUnits": 0,
  "deferredUnits": 0,
  "outOfScopeUnits": 0,
  "openUnitIds": [],
  "units": [
    {
      "id": "webhook-messaging",
      "subsystem": "payments",
      "trustBoundary": "payment-provider-to-webhook-handler",
      "attackClassId": "rpc-messaging",
      "state": "covered",
      "reasonCode": null,
      "reviewedPaths": ["docs/payments.md"],
      "evidenceRefs": [
        {
          "kind": "documentation",
          "path": "docs/payments.md",
          "lineStart": 20,
          "lineEnd": 35,
          "note": "architecture overview mentions a webhook endpoint"
        }
      ],
      "relatedFindingIds": [],
      "validationPlan": null,
      "explanation": null
    }
  ]
}
```

## Expected Behavior

- The Phase 3 validator accepts the ledger because its shape and taxonomy are valid.
- The critic should question whether documentation-only evidence supports a `covered` claim for message authentication, replay, authorization, integrity, and idempotency controls.
- The concern is claim-to-evidence mismatch, not the small number of files.
- Do not create a vulnerability finding unless defect evidence exists independently.
