# Optional Agent SDK hook adapter — `PreToolUse` / `Stop`

> **OPTIONAL. The authoritative routine gate is the local cockpit/pawl path**;
> `agent-output-validate.yml` (ag-mptr) is PR/tag/manual backstop telemetry.
> Use this only if your team wants *in-loop* interception in an Agent SDK loop.
> AgentOps 3.0 is **hookless-first** — this adapter is a convenience sample, **not**
> a dependency, **not** a hook revival, and **not** required for an agent to be
> AgentOps-native. A bypassed in-loop hook must never mean unvalidated work lands;
> that is why the deterministic cockpit/proof path — not this adapter — is the
> enforcement boundary.

## What it is

A tiny reference adapter that an Agent SDK loop can register as a `PreToolUse`
and/or `Stop` callback. It shells out to the `ao` CLI — `ao validate --gate`
(with the `standards` checklist loaded into the agent's instructions) — and lets
the agent surface the verdict in-loop. It wires into **no runtime by default**;
copy it into your own SDK harness if you want it.

**Default path (recommended):** do nothing here — let the agent run, then land
through the local cockpit/pre-push/pawl proof path. `agent-output-validate.yml`
can run `ao validate` as PR/tag/manual backstop telemetry. The adapter only adds
an *earlier, advisory* signal; it does not replace the gate of record.

## Reference samples

These type-check (`tsc` / `mypy`) but are intentionally not wired into any
runtime. They are illustration, not infrastructure.

### TypeScript (`PreToolUse`)

```ts
import { execFileSync } from "node:child_process";

// OPTIONAL in-loop advisory check. The authoritative gate is the cockpit/pawl
// proof path, not this hook.
export function preToolUseValidate(changedFiles: string[]): {
  ok: boolean;
  verdict: string;
} {
  try {
    execFileSync("ao", ["validate", "--gate", "--changes", ...changedFiles], {
      stdio: "pipe",
    });
    return { ok: true, verdict: "PASS" };
  } catch (err: unknown) {
    // exit 1 = FAIL, exit 2 = could-not-run. Advisory only — never block landing
    // on this; the cockpit/pawl proof path is the real boundary.
    const code = (err as { status?: number }).status ?? 1;
    return { ok: false, verdict: code === 2 ? "ERROR" : "FAIL" };
  }
}
```

### Python (`Stop`)

```python
import subprocess

def stop_validate(changed_files: list[str]) -> tuple[bool, str]:
    """OPTIONAL in-loop advisory check. The cockpit/pawl path is the default gate."""
    proc = subprocess.run(
        ["ao", "validate", "--gate", "--changes", *changed_files],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return True, "PASS"
    # Advisory only — do NOT hard-block on this; the cockpit/pawl proof path is
    # authoritative (Managed Agents are not ZDR; never inline holdout).
    return False, "ERROR" if proc.returncode == 2 else "FAIL"
```

## Boundaries

- **Never** register an always-on hook anywhere in this repo; this stays a sample.
- The adapter calls only `ao validate` / the `standards` checklist — it does not
  read holdout/eval corpus, and it must not be used to smuggle one in.
- If you adopt it, document in your harness that the **cockpit/pawl proof path remains the gate of record**.
