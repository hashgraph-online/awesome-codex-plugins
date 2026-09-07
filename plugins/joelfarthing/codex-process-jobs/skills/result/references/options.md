# Result options

- Default output is bounded to 65,536 bytes per stdout/stderr stream.
- `--bytes <1..1048576>` changes the per-stream bound.
- `--full` reads up to the independent 1 MiB model cap.
- Incremental reads require independent stdout and stderr byte/generation
  cursor pairs. Never combine cursor options with `--full`.
