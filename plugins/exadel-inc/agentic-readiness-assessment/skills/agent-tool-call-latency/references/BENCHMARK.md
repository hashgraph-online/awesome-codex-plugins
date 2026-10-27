# Benchmark

A benchmark separates harness overhead from the work: the same scripted calls run under two configurations that differ in one thing (permission mode, allow rules, release, shell), and the difference in fast-call latency is that thing's cost. Run one whenever a cause blames the harness rather than the command.

## Workload

One call per message, so no call waits for a sibling, and cheap calls only, so the command's own time is near zero:

```text
Latency benchmark. Make exactly ONE tool call per message, never parallel calls, no commentary between steps. Steps 1-10: first read notes.txt once, then for N from 1 to 10 edit notes.txt to change "line N: old" to "line N: new". Steps 11-20: run each as its own shell call: touch a1.txt / mkdir -p d1 / cp notes.txt c1.txt / mv a1.txt a2.txt / touch a3.txt / mkdir -p d2 / cp notes.txt c2.txt / mv a3.txt a4.txt / touch a5.txt / mkdir -p d3. Steps 21-25: run each as its own shell call: ls / cat notes.txt / wc -l notes.txt / ls d1 / head -3 notes.txt. Then reply DONE.
```

Keep it on one line: in an interactive terminal a newline submits the prompt early. Steps 11–20 write files (they exercise the approval path); steps 21–25 are read-only (they show what an allow rule saves).

## Running it

1. Make one fresh directory per configuration under a unique root, for example `/tmp/agent-latency-bench/<config>/`, with `notes.txt` holding `line 1: old` … `line 10: old`.
2. Run the harness headless in each directory: `claude -p --permission-mode <mode> "$PROMPT"` for Claude Code, `codex exec "$PROMPT"` for Codex, the equivalent for others.
3. Strip the environment you inherit: when the audit itself runs inside an agent, variables such as `CLAUDE_CODE_ENTRYPOINT` change how a child session behaves. Run through `env -i HOME="$HOME" USER="$USER" PATH="$PATH" SHELL="$SHELL" TERM=xterm-256color LANG=en_US.UTF-8 …`.
4. Change one thing between configurations. A benchmark is a long-running command: start it in the background and wait for its completion.
5. Extract only the benchmark: `extract.py --only <adapter> --since <today> --include-cwd /agent-latency-bench/ --out <work directory>/bench.jsonl`, then compare p50 per step type between the configurations' projects. The main extraction passes `--exclude-cwd /agent-latency-bench/`, so these sessions never count as the user's work.

Done when each configuration's 25 calls are present in `bench.jsonl` and the p50 difference for the step type in question is stated with both values.
