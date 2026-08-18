# Add Safe Interaction Workflow

Add prompts, progress, color, or sensitive credential entry without breaking automation.

## Steps

1. [ ] Confirm the feature is useful only in human mode.
2. [ ] Define explicit enable, disable, and noninteractive behavior.
3. [ ] Send transient progress to terminal stderr, never result stdout.
4. [ ] Make cancellation close prompts and background renderers.
5. [ ] Stop progress and restore terminal state before final results or errors render.
6. [ ] Preserve the primary failure; join or report cleanup failures without masking it.
7. [ ] Restore terminal state and stop goroutines on every return path.
8. [ ] Test non-TTY streams, `NO_COLOR`, conflicting flags, missing input, and interrupt.

## Common Mistakes

| Mistake | Corrective action |
|---|---|
| Prompting because stdin happens to be a TTY | Require interaction policy plus capability |
| Storing secrets in flags | Read without echo or use a protected input source |
| Spinner shares stdout with JSON | Use stderr in human mode and disable otherwise |

## Exit Criteria

- [ ] The feature disappears cleanly in plain and structured modes.
- [ ] No secret or terminal state leaks on failure.
