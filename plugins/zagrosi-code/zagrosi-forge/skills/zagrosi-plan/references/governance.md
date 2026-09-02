# Optional governance

Create separate ledgers only for independent audit or long-lived ownership.
Use these exact table headers:

- `decisions.md`: ID | Date | Decision | Alternatives | Rationale | Impact
- `risk-register.md`: ID | Risk | Severity | Likelihood | Mitigation | Section |
  Verification
- `traceability.md`: Requirement | Plan Coverage | Section Coverage | Test
  Coverage | Status
- `quality-gates.md`: Gate | Command | Evidence | Owner | Stop condition

Use stable `DEC-*`, `RISK-*`, and `REQ-*` IDs. Keep the plan/index authoritative;
ledgers link IDs and evidence instead of repeating narrative.
