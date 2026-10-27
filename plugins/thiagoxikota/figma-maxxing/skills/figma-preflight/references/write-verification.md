# write verification

Use only the section relevant to the current operation. Inline `scripts/` and `references/` paths are relative to this skill’s directory unless a link says otherwise. Existing authorization and the entrypoint contract govern these recipes.

## Post-approval: write execution rules

After the preflight OK, BEFORE generating any JS for `figma_execute` (or `use_figma` on path B):

1. Use only the API/layout/data/recovery references applicable to the operation; naming applies to new layers. Reuse current validated context.
2. When the write finishes (or aborts): release the lock with
   `python3 "${CLAUDE_SKILL_DIR}/scripts/figma_lock.py" release <fileKey> --agent <agent> --task <task>`. Forgetting to
   release blocks future sessions until the TTL expires.
3. Never send the known failing patterns: a sync `figma.currentPage = X` assignment, a missing
   `await` on an async call, `figma.notify()`, `setPluginData`, `createConnector`. The optional
   precheck hook (`hooks/figma-canon-precheck.py` at the root of the figma-maxxing repo, opt-in)
   flags these patterns. If it fires:
   read the message, fix it at the source, do NOT retry blindly.
4. **Check the ancestor chain for `locked` (field note, 2026-08).** In one large bind sweep
   through the figma-console bridge, a handful of binds under a GROUP with `locked: true` did not
   take, with no error, while each node read `locked: false`. Figma's typings say `locked` does
   not affect plugin writes, and the cause is not established. The check is cheap: in a write that
   sweeps a tree, check the chain (`for (let p=n; p; p=p.parent) if (p.locked) ...`), not only the
   target, and rely on the read-back in rule 5 either way.
5. **Post-write verification reads the PROPERTY YOU CHANGED, never a proxy.** In that same batch
   the read-back checked color and opacity and came back green on the nodes that were never
   written: color and opacity really had not changed, precisely because nothing happened. If you
   bound a variable, read `boundVariables[prop][i]`. If you created a node, read its id in the
   parent. An independent count AFTER the batch, compared against the expected number, is the
   only closure that counts.
