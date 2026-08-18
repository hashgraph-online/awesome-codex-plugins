# Editing Review Knowledge

Editing developer docs is a quality pass on both information and reader flow. It should test whether the doc works, not only whether the prose sounds polished.

Source basis: *Docs for Developers*, Chapter 4, "Editing documentation"; *The Product Is Docs*, Chapter 15, "Technical Editing," and Chapter 16, "Technical Verification."

## Editing Passes

| Pass | Checks |
|------|--------|
| Technical accuracy | Facts, code, commands, UI labels, API details, outputs, warnings |
| Completeness | Prerequisites, missing steps, supported versions, next steps, recovery paths |
| Structure | Title, headings, order, templates, prerequisites, links, next steps |
| Clarity | Ambiguous phrasing, unexplained terms, hidden assumptions, hard-to-follow steps |
| Brevity | Duplication, irrelevant background, bloated sentences, unnecessary caveats |

## Review Types

- **Self-review**: The author checks structure, flow, and obvious gaps before asking others.
- **Peer review**: Another writer or teammate checks usability and clarity.
- **Technical review**: A subject-matter expert verifies facts, examples, and implementation details.

## Feedback Integration

Review comments are inputs, not commands. Resolve conflicts by returning to the reader goal, source of truth, risk, and evidence.

## Technical Editing Scope

Technical editing is more than copyediting. It checks whether the content is accessible, clear, usable, relevant, cohesive, consistent in terminology, appropriate for the audience, and scoped to the learning objective. Editing can happen before, during, or after drafting; the most useful edit depends on the writer's timing and the release risk.

Fast product cycles benefit from smaller edit units. A single topic, section, or pull request can receive focused feedback faster than a large manual or doc set.

## Technical Verification

Technical verification confirms that documentation is accurate enough for users to rely on. Start from the assumption that technical material needs review by someone other than the writer, then carve out exceptions based on risk.

| Review Type | Use For |
|-------------|---------|
| Spot review | Confirming an assumption, setting, edge case, or unclear concept while writing |
| Draft review | Written review of a near-complete topic or doc set |
| QA review | Testing procedures, migrations, upgrades, or risky workflows |
| Review meeting | Resolving missing, shallow, or conflicting written reviews |

QA testing is most valuable for complex, multistep, hard-to-set-up, destructive, high-commitment, edge-case-heavy, or hard-to-verify procedures. Migration, upgrade, data transformation, and recovery procedures usually deserve formal testing.

## Reviewer Routing

Target reviewers by what they can verify:

- Responsible engineer: behavior, limits, API details, implementation consequences.
- Product manager: user goals, use cases, release scope, and product fit.
- QA: procedure correctness, edge cases, test environments, success criteria.
- Support, field, education, or customer success: customer pain, terminology, and common failure modes.
- Peer writer or editor: usability, clarity, consistency, information design, and style.

Ask reviewers specific questions and send small chunks when possible. Track review requests in the team's normal tooling and keep written confirmation for high-risk procedure testing.

## Common Misconceptions

- **Myth**: Editing means fixing grammar at the end.
  **Reality**: Accuracy, completeness, and structure usually matter more.
- **Myth**: Accepting every reviewer suggestion is safest.
  **Reality**: Blindly accepting feedback can create inconsistency or drift from user needs.
- **Myth**: Technical review can happen after publish.
  **Reality**: High-risk procedures and examples need validation before release.
- **Myth**: A shallow "looks good" review is enough.
  **Reality**: Review quality matters; missing or incomplete verification leaves the writer accountable for reader failure.
- **Myth**: Editing must wait until the full draft is finished.
  **Reality**: Planning, outline, single-topic, side-by-side, and post-release edits can all improve quality depending on timing.

## Rules And Checks

Use these rules when editing or reviewing developer documentation.

## Core Rules

1. **Edit in passes** - Accuracy, completeness, structure, clarity, and brevity catch different failures.
2. **Verify runnable claims** - Commands, procedures, examples, links, and outputs need evidence or a clear limitation.
3. **Check prerequisites before first action** - Missing setup blocks readers even when later steps are correct.
4. **Prioritize reader risk** - Data loss, security exposure, failed commands, and broken setup outrank style issues.
5. **Use source-of-truth review** - Route API, SDK, UI, security, legal, and release facts to the right owner.
6. **Keep structure aligned to goal** - Title, headings, order, and next steps should support the doc's purpose.
7. **Cut duplication and vague language** - Remove repeated ideas, inconsistent terms, idioms, and biased wording.
8. **Request specific feedback** - Ask reviewers to check named sections, claims, examples, or risks.
9. **Resolve conflicts through user need** - When comments disagree, choose the option that best serves the target reader.
10. **Prepare before review** - Self-edit first so reviewers spend attention on content, not avoidable noise.
11. **Target essential reviewers** - Assign required reviewers individually and make each role clear.
12. **Use QA for risky procedures** - Formal procedure testing belongs in the release path when user harm or complex setup is possible.
13. **Track incomplete reviews** - Missing, vague, or contradictory review is an unresolved risk, not approval.
14. **Capture confirmation** - For high-risk docs, preserve written review or test results.

## Risk Order

| Priority | Examples |
|----------|----------|
| Highest | Security, privacy, data loss, irreversible operations |
| High | Broken commands, incorrect API details, missing prerequisites, failed migrations |
| Medium | Confusing order, missing context, weak troubleshooting |
| Lower | Style preferences, minor wording, formatting polish |

## Red Flags

- A procedure has not been executed or simulated.
- The doc includes "just", "simply", or other language that hides complexity.
- Review comments ask for broad "looks good?" feedback.
- Multiple terms describe the same product concept.
- The doc has no next step, expected result, or recovery path.
- Required reviewers are copied as a group with no specific assignment.
- QA has not tested a procedure that can alter data, affect production, or consume significant resources.
- A reviewer approved the doc but did not check the risky sections.


## Examples And Patterns

Use these examples to shape review output and feedback.

## Review Finding Pattern

```text
Finding: The setup section never states that webhook signing requires API version 2025-01 or later.
Risk: Users on older accounts will follow the guide and receive an unsupported-header error.
Evidence needed: Confirm version gate with API owner.
Fix: Add the version prerequisite before the first setup command and link to the migration guide.
```

## Specific Review Request

Weak:

```text
Can you review this?
```

Better:

```text
Can you verify the Node.js signature example, the expected error codes, and whether the dashboard label is still "Signing secret"?
```

## Verification Routing Pattern

```text
Doc: Upgrade production workspace to the new auth flow
Risk: Production access and irreversible configuration changes
Required review: Auth engineer for behavior, PM for support window, QA for procedure test, support for common failure modes
QA test request: Run the procedure in a staging workspace with an old-token account and confirm expected login, rollback, and error states
Release blocker: Publish only after QA records pass/fail result or owner accepts residual risk
```

## Feedback Integration

Scenario: One reviewer asks for a long architecture explanation in a how-to guide; another asks to keep the guide task-focused.

Resolution:

- Keep the how-to focused on the task.
- Add one short explanation only where it affects the user's decision.
- Link to a concept page for the full architecture.

## Clarity Rewrite

Weak:

```text
Simply configure the app with the appropriate credentials.
```

Better:

```text
Set `PAYMENTS_API_KEY` to a test-mode API key from the dashboard.
```
