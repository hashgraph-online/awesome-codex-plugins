<div align="center">

# AgentOps

### Fresh-context validation for coding-agent work

Coding agents are stochastic and can declare work done when it is not.
AgentOps turns one behavior into one bounded experiment, gives the exact result
to a fresh validator, and stores the verdict under your control.

</div>

```text
RPI -> Plan -> Implement -> fresh Validate -> durable verdict -> report and stop
```

## Install

```bash
# Install the optional CLI.
brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops
brew install agentops

# Keep one canonical checkout and link it into every installed runtime.
git clone https://github.com/boshu2/agentops.git ~/.local/share/agentops
cd ~/.local/share/agentops
ao skills link
```

`ao skills link` creates source symlinks under the portable
`~/.agents/skills` root and every detected runtime skill root, including Claude,
Codex, Gemini/Antigravity, and Cursor. It never replaces a real directory or a
foreign symlink. Updates stay simple:

```bash
cd ~/.local/share/agentops
git pull --ff-only
ao skills link
```

Without Homebrew, build the optional CLI from the checkout and then link:

```bash
cd ~/.local/share/agentops/cli
go install ./cmd/ao
cd ..
"$(go env GOPATH)/bin/ao" skills link
```

The 3.x runtime plugin installers remain only as migration compatibility for
this release. New installs do not need a plugin cache, hooks, or a runtime-owned
copy of the AgentOps corpus. See the [migration guide](docs/MIGRATION.md) for
removing an old plugin install.

## Core workflow

```text
> use plan for "rate-limit /login"
PlanPacket: normal + burst edge scenarios, exact scope, first acceptance check

> use implement
CandidatePacket: RED -> GREEN -> refactor, actual paths, content manifest

> use validate
verdict.v2: FAIL — burst refill violates scenario S2
checked: S1, S2, subject identity, write scope
not_checked: load behavior above declared limit
```

Or invoke `rpi` with `rate-limit /login` to run the three responsibilities once and
receive one report. RPI stops after `PASS`, `FAIL`, or `NOT_PROVEN`; the caller
decides whether to revise, deliver, or abandon the work.

## Core skills

| Skill | Responsibility |
|---|---|
| `rpi` | invoke Plan, Implement, and fresh Validate at most once |
| `plan` | define one behavior, acceptance, evidence, and write scope |
| `implement` | run one bounded experiment and describe the candidate |
| `validate` | independently judge exact content and persist `verdict.v2` |

`learn` is an optional later analysis of verdict collections. `premortem`,
`postmortem`, `council`, and idea genies are caller-selected strategies.
Factory/runtime skills such as NTM, Agent Mail, Gas City, and swarms are optional
adapters. None can change core sequencing or a verdict.

## The evidence contract

A PASS binds:

- unchanged acceptance;
- a deterministic manifest of files, symlinks, deletions, executable bits, and
  content digests;
- complete changed-path coverage inside the Plan write scope;
- distinct author and validator context IDs;
- an explicit freshness attestation;
- criterion results, evidence references, checked scope, and omissions.

Missing identity, mutation, or incomplete coverage is `NOT_PROVEN`. A proven
out-of-scope change or failed acceptance criterion is `FAIL`.

Verdicts default to `.agentops/verdicts/sha256/<digest>.json`. They are plain,
content-addressed JSON and do not require Git, `ao`, a tracker, a hosted service,
or a provenance ledger.

## Product boundary

AgentOps owns intent shaping, one bounded experiment, exact content identity,
independent judgment, and the durable verdict. It does not own retries, budgets,
queues, work claims, Git, CI, PRs, merges, closure, release, or delivery.

Use your repository's existing direct-push, PR, merge queue, hosted CI, and
release process after validation. Local and cloud agents use the same packet and
verdict contracts.

## Honest status

Fresh independent judgment is a practical trust boundary, not a guarantee that
stochastic output is correct. Context identities and freshness are declared
facts, not cryptographic isolation. The longer-term learning hypothesis—that
recurring verdict findings can improve future context and deterministic
checks—remains off the critical path and must be measured.

[Product boundary](PRODUCT.md) · [Operating loop](docs/architecture/operating-loop.md) · [CLI commands](cli/docs/COMMANDS.md) · [Skill router](docs/SKILL-ROUTER.md) · [Docs index](docs/documentation-index.md)

Contributing: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). License: Apache-2.0.
