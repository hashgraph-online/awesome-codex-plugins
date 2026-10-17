# Contract Examples

Use these shapes as short references. Omit `_runtimeContext` and `_runtimeProof`; the trusted Hook
adds them.

## Good Checklist

Goal: publish a working command-line importer.

- `C1` Imported records are correct and deduplicated.
  - `C1.1` Supported input parses successfully.
  - `C1.2` Duplicate records are merged by the documented key.
- `C2` Operators can run and diagnose the importer.
  - `C2.1` Help and error output are actionable.
  - `C2.2` Installation and rollback are verified.

These are observable results. Their child items measure only their parent.

## Bad Checklist

- Read the repository.
- Make a plan.
- Connect tools.
- Implement things.
- Test it.

These are actions or generic phases. They do not say what accepted result exists.

## Initialize

Omit `contractId`; the plugin returns it after saving.

```json
{
  "source": "model-generated",
  "objectives": [
    {
      "id": "C1",
      "title": "Imported records are correct and deduplicated",
      "contributionBps": 6500,
      "contributionReason": "Correct imported data is the primary product result",
      "status": "active",
      "evidence": [],
      "items": [
        {
          "id": "C1.1",
          "title": "Supported input parses successfully",
          "status": "active",
          "evidence": []
        }
      ]
    },
    {
      "id": "C2",
      "title": "Operators can run and diagnose the importer",
      "contributionBps": 3500,
      "contributionReason": "The result must be usable and recoverable",
      "status": "pending",
      "evidence": [],
      "items": []
    }
  ]
}
```

## Update

Replace the sample `gp_importer01` with the actual `contractId` returned by the tool. Copy the latest revision too.

```json
{
  "contractId": "gp_importer01",
  "expectedRevision": 3,
  "changes": [
    {
      "targetId": "C1.1",
      "status": "completed",
      "evidence": [
        {
          "id": "parser-test",
          "kind": "test",
          "verification": "reported",
          "summary": "The parser test completed successfully",
          "observedAt": "2026-08-18T00:00:00.000Z",
          "source": "model"
        }
      ]
    }
  ]
}
```

## Rescope

Send the full replacement objective set, the current revision, and a short reason. Recalculate
contributions so required non-cancelled objectives total `10000`. Preserve IDs for unchanged
results.

Never send `overallProgress`, `overallPercent`, weights in a normal update, or a new session ID.
