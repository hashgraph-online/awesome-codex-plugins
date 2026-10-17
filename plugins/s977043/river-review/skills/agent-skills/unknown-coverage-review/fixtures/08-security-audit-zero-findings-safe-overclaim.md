# Test Case: Zero findings plus safety claim is an overclaim

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
      "id": "authz-focused",
      "subsystem": "auth",
      "trustBoundary": "api-to-authorization-service",
      "attackClassId": "authn-authz",
      "state": "covered",
      "reasonCode": null,
      "reviewedPaths": ["src/auth/authorize.mjs"],
      "evidenceRefs": [
        {
          "kind": "source",
          "path": "src/auth/authorize.mjs",
          "lineStart": 20,
          "lineEnd": 88,
          "note": "default-deny and ownership checks inspected"
        }
      ],
      "relatedFindingIds": [],
      "validationPlan": null,
      "explanation": null
    }
  ]
}
```

## Draft audit summary

> No findings were found, all planned units are covered, and `openUnitIds` is empty. Therefore this subsystem is secure and has no vulnerabilities.

## Expected Behavior

- Report a safety-overclaim residual because the conclusion exceeds what source-only coverage evidence proves.
- Do not downgrade the `covered` state merely because there are zero findings.
- Do not turn the critic observation into a deterministic Gate decision in Phase 4.
