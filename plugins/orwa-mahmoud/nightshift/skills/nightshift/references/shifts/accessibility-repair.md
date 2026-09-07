# Accessibility repair — finite — objective violations from checks the project already runs

Accessibility violations reported by the repository's configured linter, test suite, or scanner.
The shift repairs concrete findings without redesigning the interface or claiming compliance.

Supported on projects that already configure accessibility lint rules or automated accessibility
tests. Detect those commands from package scripts, test configuration, or the item gate. If the
project has no established accessibility check, this shift is unsupported and must not start.
Never select this entry in artifact mode. Do not `git init` a notes folder to make findings commitable.

```text
- [ ] **Accessibility repair — fix objective violations reported by existing project checks.**
  - Never select this entry when work mode is artifact.
  - Discovery: detect and run the repository's configured accessibility linter, component tests,
    or automated scanner. Record the command and objective reported violations; dedupe against
    snag-log.md (ALL seen — fixed and rejected). Do not add a scanner silently.
  - Repair one related cluster at a time using the product's existing design system and semantic
    patterns. Preserve intended behaviour and appearance, rerun the accessibility check and item
    gate, commit.
  - Park findings that require visual design, product copy, legal interpretation, assistive-
    technology judgment, or an owner tradeoff; include the rule, affected surface, and evidence.
  - Never perform an unrelated visual redesign or rewrite product copy to satisfy a scanner.
  - Never suppress a rule, hide an element from assistive technology, or weaken a test merely to
    clear the report.
  - Never claim WCAG, legal, or full accessibility compliance from automated checks alone.
  - Ends when the same configured checks report no actionable objective violations, and every
    judgment-dependent finding is parked with its evidence and required decision.
  - Verify: the item gate is green at every commit; rerun the project's configured accessibility
    checks after each cluster and once more over the complete affected surface.
```
