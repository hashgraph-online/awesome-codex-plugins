# Test Case: Zero findings with neutral source-only language is not a problem

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

> No findings were established in the investigated source surfaces. The recorded unit has source evidence, but this source-only audit does not establish the absence of vulnerabilities.

## Expected Behavior

- Do not report a safety-overclaim residual.
- Do not report a coverage gap solely because `relatedFindingIds` is empty.
- Preserve the source-only limitation without claiming security completeness.
