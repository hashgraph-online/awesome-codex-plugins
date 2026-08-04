# Focused Re-review Prompt Template

Use this template after a wave has a current failed receipt. It narrows review
to the declared repair and preserves the normal review receipt gate.

```
Subagent (general-purpose):
  description: "Focused re-review of wave [WAVE_ID], repair round [REPAIR_ROUND]"
  model: [MODEL — REQUIRED: resolve the review profile]
  prompt: |
    You are re-reviewing a focused repair for wave [WAVE_ID].

    ## CLI repair evidence

    The controller read `ssf execution show <change-dir> --json` before this
    dispatch. The current repair status is [REPAIR_STATUS], round is
    [REPAIR_ROUND], and the prior review head is [PREVIOUS_HEAD]. Read the
    previous review report at [PREVIOUS_REVIEW_REPORT] first.

    ## Scoped diff under review

    **Base:** [PREVIOUS_HEAD]
    **Head:** [HEAD_SHA]
    **Diff file:** [SCOPED_DIFF_FILE]

    Review only this scoped diff and the prior finding. Confirm whether the
    repair resolves that finding, creates a regression, or expands beyond the
    declared repair scope. Do not re-run a broad review, modify the worktree,
    or edit receipt and repair-state files.

    Rounds 1–3 are recovery rounds. Rounds 4–5 are escalation rounds: require
    explicit evidence of why prior recovery did not resolve the finding. If the
    CLI status is `adjudication-required`, do not request a sixth repair;
    document the unresolved issue for human adjudication.

    ## Output

    Write a distinct non-empty review report to `[CHANGE_DIR]/.superpowers/sdd/reviews/[WAVE_ID]-rereview.md`, with the
    prior finding, scoped-diff evidence, verdict, and file:line references.
    Then provide exactly this receipt command to the controller:

    ```bash
    ssf execution review <change-dir> --wave [WAVE_ID] --base [PREVIOUS_HEAD] --head [HEAD_SHA] --report [REVIEW_REPORT_FILE] --verdict <pass|fail>
    ```

    Use `fail` for any unresolved Critical or Important finding. The controller
    records receipts through the CLI; you must not directly change state files.
```

**Required placeholders:** `[MODEL]`, `[WAVE_ID]`, `[REPAIR_STATUS]`,
`[REPAIR_ROUND]`, `[PREVIOUS_HEAD]`, `[PREVIOUS_REVIEW_REPORT]`, `[HEAD_SHA]`,
`[SCOPED_DIFF_FILE]`, `[REVIEW_REPORT_FILE]`.
