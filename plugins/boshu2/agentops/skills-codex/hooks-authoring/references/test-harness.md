# Hook Test Harness

Use this reference when building or reviewing hook tests.

## Fixture Shape

Keep fixtures small and representative:

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "git status --short"
  },
  "cwd": "/repo",
  "session_id": "test-session"
}
```

Include at least one allow fixture and one block fixture for each blocking hook.

## Direct Test Loop

```bash
printf '%s\n' "$fixture_json" | hooks/<hook>.sh
status=$?
```

Assert all three outputs:

- Exit code.
- Stdout JSON, when structured output is expected.
- Stderr block reason, when exit code is `2`.

## Self-Tests

AgentOps ships no hook gates (3.0 is hookless). Validate your own hooks
directly:

```bash
# Validate the manifest shape against the schema
jq empty your-hooks.json && \
  ajv validate -s schemas/hooks-manifest.v1.schema.json -d your-hooks.json

# Lint your hook scripts
find . -name "*.sh" -path '*hooks*' -print0 | xargs -0 shellcheck --severity=error

# Assert output shape + exit codes with representative fixtures
printf '%s' '{"tool_input":{"command":"git push -f origin main"}}' | bash your-hook.sh; echo "exit: $?"
```

Keep hook output to the portable subset both Claude and Codex accept (avoid
`hookSpecificOutput.updatedInput`, which Codex silently drops).
