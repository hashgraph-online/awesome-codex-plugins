# Skill Anti-Patterns

**Purpose**: Prevent common failures in skill authoring.

## Avoid

- descriptions that are too vague to trigger reliably
- descriptions that say what the skill is but not when to use it
- no positive/negative/boundary trigger examples
- no near-miss case, so trigger stealing by a neighboring skill is never measured
- `SKILL.md` bodies that become mini-wikis
- core trigger or stop-condition logic hidden in references
- duplicated detail across core, rules, and references
- references nested so deeply they are hard to discover
- extra docs like `README.md`, `CHANGELOG.md`, or `QUICK_REFERENCE.md` inside the skill unless a runtime or user explicitly needs them
- time-sensitive provider details in canonical core instructions
- scripts added without a clear reliability justification, usage, dependency, and failure behavior
- assets that are never copied, filled, or used by the workflow
- provider docs or retrieved snippets treated as higher authority than user/project instructions
- credential, network, destructive, or production side effects without explicit gates
- too many options when the skill should recommend a path
- a loop without feedback, metric or rubric, independent guard, acceptance rule, and hard stop
- changing the baseline or eval set and calling the result an improvement
- provider-specific commands in the shared core with no capability check or explicit degradation path
- source dates later than the actual verification run, or snippets/model summaries recorded as sources
- structural bilingual pairing treated as proof of equivalent behavior
- final-output-only validation for workflows where tool arguments, ownership, permissions, or side effects matter
- a trigger case that inherits its `runs` or `threshold` instead of stating them
- a description grown past the per-entry limit while being optimized, without re-checking the limit
- an assertion that passes in **both** the with-skill and without-skill arms, which inflates the pass rate without reflecting the skill's value
- a `grading.json` record with `passed: true` and no **evidence string**
- execution results kept inside the shipped skill folder instead of under `.omo/evidence/`
- a skill that restates what the agent already does reliably, which is cost without benefit
- `allowed-tools` presented as a permission boundary rather than a convenience grant
- a runtime-only frontmatter field (`disable-model-invocation`, `when_to_use`, `agents/openai.yaml`) that carries part of the contract unlabelled, so the skill behaves differently on another runtime (SK-P-3)
- a deploy, publish, send, or delete skill left open to automatic activation
- volatile dates, counts, or version pins in the loaded head of `SKILL.md`, so every refresh invalidates cached reuse
- two eval sets - `assets/evals/` and a packaged tool's case file - that have drifted apart
- "the skill is well written, so it helps" offered as a utility claim without a paired baseline
- human review recorded as "looks bad" instead of a specific, actionable complaint
- an unattended loop or a fan-out with no numeric cap, no independent checker, or no declared join shape

## The Artifact Audit

These test what a skill **is**, not what it receives. A skill is distributed code plus instructions, so audit it before shipping. All seven rows, not a subset:

| Category | What to look at | Severity as assigned by the source |
|---|---|---|
| Code execution | Scripts in the skill directory (`*.py`, `*.sh`, `*.js`). Scripts run with full environment access | High |
| Instruction manipulation | Directives to ignore safety rules, hide actions from users, or alter behavior conditionally | High |
| MCP server reference | References shaped like `ServerName:tool_name` | High |
| Network access | URLs, API endpoints, `fetch`, `curl`, `requests` | High |
| Hardcoded credentials | Keys, tokens, and passwords inside skill files or scripts | High |
| Filesystem scope | Paths outside the skill directory, broad globs, `../` | Medium |
| Tool invocations | Instructions directing the agent to use bash, file operations, or other tools | Medium |

- SK-A-1: Audit a skill against the seven categories above before distributing it, and record the result.
- SK-A-2: Do not distribute a skill from an untrusted source without a full audit.
- SK-A-3: Pin a skill to a version, and re-review it when the version changes.

**This package is a code-execution instance of its own audit.** `skills/hyper-skill/scripts/validate-hyper-skill.sh` is executable code inside a distributed skill directory, so the High code-execution row applies to `hyper-skill` itself. Audit it as a subject, not only as a checklist.

## Red Flags

- "This skill helps with many things."
- "See references/" without saying when to read which file.
- "Use the latest best practice" without a source ledger or refresh condition.
- "There are five approaches" without a recommended decision path.
- multiple files repeating the same definitions
- old provider guidance mixed into current core rules
- local `instructions/skill/` guidance ignored during non-trivial skill changes
- validation omitted because "the structure looks good"
- "The agent can keep trying" without a budget or keep/discard rule.
- "Use whatever tool is available" without preserving outcome, safety, and failure semantics.
- a child agent's success claim used as parent verification
- "it passed" without the evidence string that says what passed

## Repair Pattern

When one of these appears:

1. Restate the skill as a triggerable execution package.
2. Rewrite `description` and trigger examples, including a near-miss case.
3. Move misplaced detail to rules, references, scripts, or assets.
4. Add or update the instruction contract.
5. Add an explicit no-loop/loop policy, runtime capability boundary, source/retrieval guard, and risk-proportional eval surface.
6. Run the seven-row artifact audit and record the result.
7. Rerun the same baseline plus adversarial and known-regression cases, inspect the trace, and record `ship`, `iterate`, `caveated ship`, or `block`.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The seven risk-tier rows with their severity labels, and version pinning with re-review | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise> |
| The with/without arms and the evidence string behind the both-arms and `grading.json` anti-patterns | <https://agentskills.io/skill-creation/evaluating-skills> |
| Results kept outside the skill folder, behind the `.omo/evidence/` anti-pattern | <https://agentskills.io/skill-creation/evaluating-skills> |
| The removal test behind the "restates what the agent already does" anti-pattern | <https://agentskills.io/skill-creation/best-practices> |
| `allowed-tools` as a permissive grant rather than a boundary | <https://code.claude.com/docs/en/skills> |
| Manual-only switches, runtime-only extension fields, and the hard error for non-spec fields on upload | <https://code.claude.com/docs/en/skills> |
| Human review as a specific per-case complaint in `feedback.json` | <https://agentskills.io/skill-creation/evaluating-skills> |
| The paired benchmark that found most public skills had no significant effect | <https://arxiv.org/abs/2603.15401> |
| Volatile values out of the loaded head | `instructions/cache/CACHE.md` §3 |
| Outer-loop caps and checker separation, and graph fan-out caps and join shape | `instructions/loop-engineering/LOOP_ENGINEERING.md`, `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| The description length limit that must be re-checked while optimizing | <https://agentskills.io/specification> |

### Evidence grade

The severity labels are `VENDOR` - that page's assignment, not a controlled study. An audit against them
catches known artifact-level problems; it is not a proof of safety. The remaining anti-patterns are
derived from the cited pages and from defects observed in this repository.
