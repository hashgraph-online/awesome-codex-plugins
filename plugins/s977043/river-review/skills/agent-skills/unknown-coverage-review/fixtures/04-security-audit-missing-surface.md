# Test Case: Security Audit missing expected surface

## Invocation

- profile: `security-audit`
- caller: `river-review-security-audit`
- mode: `focused`
- schema validation: pass
- semantic validation: pass

## Reconnaissance expected scope

```text
payments × payment-provider-to-webhook-handler × rpc-messaging
payments × api-to-payment-service × authn-authz
```

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
      "id": "payment-webhook",
      "subsystem": "payments",
      "trustBoundary": "payment-provider-to-webhook-handler",
      "attackClassId": "rpc-messaging",
      "state": "covered",
      "reasonCode": null,
      "reviewedPaths": ["src/payments/webhook.mjs"],
      "evidenceRefs": [
        {
          "kind": "source",
          "path": "src/payments/webhook.mjs",
          "lineStart": 10,
          "lineEnd": 120,
          "note": "signature, replay, and idempotency paths inspected"
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

- Surface `payments × api-to-payment-service × authn-authz` as an unexplained coverage omission because reconnaissance planned it independently of the ledger.
- Ask for the missing unit to be recorded with the normal Phase 3 state vocabulary.
- Do not fabricate a vulnerability finding or a Gate decision from the omission.
- Do not interpret empty `openUnitIds` as complete semantic coverage.
