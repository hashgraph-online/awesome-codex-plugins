# Advanced completion evidence

Read this only for ambiguous completion evidence, an explicit audit, a failed
completion correction, or enforced visual/result/UI/scope proof obligations.
Ordinary unambiguous endings need no manual staging. All commands and private
bindings stay outside user-facing replies.

10. Before claiming full completion for an active guarded task, check that
   every open item has matching successful evidence. Ordinary endings need no
   commands: when the final reply shows a verifiable whole completion, the
   guard binds the unique successful evidence itself and closes the current
   work unit; waiting or deferred boundaries end silently. If evidence is not
   unique, the item stays open and one correction may ask for an explicit
   selection. The advanced command path exists for genuinely ambiguous cases:
   - Inspect the private ledger with the injected `checkpoint-status` command.
     Its default view is bounded to the current work unit and descendants and
     lists ancestor constraints separately. Use `--full` or `--item ID` only
     for explicit audit.
   - Inspect each item's `verification.mode`. `legacy_fallback` intentionally
     uses the compatible successful-evidence rule and remains visible as a
     degradation. For `enforced`, satisfy every listed obligation.
   - Select only successful `E####` evidence printed by that command. Plain-text
     tool output without a structured success status or an exact authoritative
     completion marker is recorded as `unknown` and cannot close an item.
     For string-only shell tools, make the verification command fail on any
     unmet condition and print a final standalone `Script completed` or
     `Command completed` line only after every check passes. The marker is
     exact and must not have trailing punctuation.
   - Ordinary non-visual proofs need no proof file: when
     `stage-checkpoint` runs, the runtime derives the artifact-surface subject
     readbacks and exactly verifiable scope coverage automatically from the
     private ledger and the successful evidence it already recorded. An
     artifact readback binds only to evidence whose input actually read the
     subject through a registered read path; a path echoed in tool output is
     not a readback. Never write or mention that derivation in the
     user-facing reply.
   - For every remaining enforced obligation — visual inspection, distinct
     result readback, UI-surface readback, or a scope the runtime could not
     verify exactly — prepare a bounded JSON manifest and run the injected
     `register-proof --manifest /path/to/proof.json` command. A proof binds
     the item, obligation, successful evidence, surface, and subjects. Visual
     inspection records immutable asset-bound facts; result readback uses a
     distinct hashed asset and resolves every fact. The runtime computes
     counts and hashes, requires the expected set to match the prompt-derived
     cardinality/digest, and rejects a proper subset. Qualitative uses of
     `all`/`完整` without a constructible expected scope remain visibly
     `legacy_fallback` rather than becoming an enforced contract.
   - Run the injected `stage-checkpoint` command with one
     `--requirement ID=E####[,E####]` flag for each pending requirement and one
     `--acceptance ID=E####[,E####]` flag for each pending acceptance item.
     The command performs a read-only precheck; the `PostToolUse` Hook commits
     the request to private plugin data outside the workspace sandbox. A
     successful staging is silent; no receipt is printed into the event stream.
   - If staging fails, continue working or report the task as incomplete.
11. Never stage both a completion checkpoint and an incomplete-turn disposition.
    `complete` is not a `stage-disposition` value; it is derived only from a
    validated private checkpoint.
12. After any private staging, send a normal concise final response with no
    checkpoint or disposition footer. The Stop Hook validates the private
    turn-bound record. At most one Stop correction can interrupt a turn;
    after it, unresolved work stays pending and the turn ends safely.

Previously passed items carry their authenticated evidence forward. A new user
turn invalidates any unstaged or unused completion attempt from the prior turn.
