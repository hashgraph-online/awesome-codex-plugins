# Workflow Contract

Every durable artifact should include a machine-readable `FORGE_META` block near
the top:

```markdown
<!-- FORGE_META
{
  "artifact_type": "implementation_plan",
  "workflow": "zagrosi-plan",
  "depth_mode": "standard",
  "source": "spec.md",
  "requirement_ids": ["REQ-001", "REQ-002"]
}
END_FORGE_META -->
```

Supported `artifact_type` values:

- `project_manifest`
- `split_spec`
- `normalized_spec`
- `research`
- `implementation_plan`
- `tdd_plan`
- `section_index`
- `implementation_section`
- `review`
- `decision_log`
- `risk_register`
- `traceability_matrix`

Use stable IDs:

- requirements: `REQ-001`
- decisions: `DEC-001`
- risks: `RISK-001`
- sections: `section-01-name`

Trace every `REQ-*` through the normalized spec, plan, TDD plan, sections, and
tests.
