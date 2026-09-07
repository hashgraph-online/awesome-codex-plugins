---
name: diagnose
description: "Systematic debugging and refactor analysis. Diagnosis before prescription. Bug mode: reproduce, trace, isolate, hypothesize, diagnose. Refactor mode: map, trace deps, measure coupling, risks, diagnose."
user-invocable: true
allowed-tools: Agent, Bash, Read, Write, Grep, Glob
kernel:
  kind: workflow
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="diagnose">

<purpose>
Diagnose before fixing. The debug skill holds the methodology; this workflow orchestrates it.
Mixing diagnosis with implementation means the surgeon starts cutting before the X-ray.
/kernel:diagnose is the X-ray.
</purpose>

<on_start>
agentdb recall "<exact error> <subsystem> <test> <files/symbols>" --global
# Recall again after isolation reveals better symbols, when the hypothesis changes,
# or when a different failure appears.
</on_start>

<skill_load>
Load: skills/debug/SKILL.md, skills/build/reference/testing.md, skills/architecture/SKILL.md
</skill_load>

<modes>
  <mode id="bug" default="true">
    <trigger>error, failing test, stack trace, "not working", exception, crash</trigger>
    <steps>
      <step id="reproduce">
        Read error output, failing test, or stack trace.
        Run the failing command/test to confirm reproduction.
        If not reproducible, document conditions and ask for more info.
      </step>
      <step id="trace">
        Follow the call stack from error to origin.
        Check recent git changes: git log --oneline --since="3 days" -- {affected files}
        Identify when the behavior changed.
      </step>
      <step id="isolate">
        Run failing test in isolation (not full suite).
        If multiple tests fail, find the minimal reproduction.
        Binary search: comment out code blocks to narrow the cause.
      </step>
      <step id="hypothesize">
        Form 2-3 hypotheses for root cause.
        For each hypothesis: what evidence would confirm or reject it?
        Test each hypothesis with minimal code changes or debug output.

        <ask_user>
          Use AskUserQuestion when: hypotheses formed and user may have domain knowledge
          Ask: "Top hypothesis: {hypothesis}. Does this match what you're seeing, or is there context I'm missing?"
          Options: investigate that, I have more context, try a different hypothesis
        </ask_user>
      </step>
      <step id="diagnose">
        Identify confirmed root cause.
        List affected files and blast radius.
        Recommend fix approach (don't implement yet).
        Determine tier based on blast radius.
      </step>
      <step id="handoff">
        Output structured diagnosis.
        Hand off to /kernel:ingest or /kernel:forge for implementation.
        If the user wants to fix immediately, transition to execute mode.
      </step>
    </steps>
  </mode>

  <mode id="refactor">
    <trigger>refactor, restructure, "clean up", "simplify", coupling, dependency</trigger>
    <steps>
      <step id="map">
        Identify all files/modules touched by the refactor target.
        Use Grep/Glob to find all references.
        Build a dependency map of what imports/calls what.
      </step>
      <step id="trace_deps">
        For each file in the map: who calls this? who depends on it?
        What breaks if this changes?
        Identify the blast radius.
      </step>
      <step id="measure_coupling">
        How tangled is this code with the rest of the system?
        Count cross-module references.
        Identify circular dependencies.
      </step>
      <step id="risks">
        What are the edge cases in the current implementation?
        What tests exist? What's untested?
        What invariants must be preserved?
      </step>
      <step id="diagnose">
        Produce restructuring plan with safety constraints.
        List files that change, in what order.
        Identify tests that must pass before AND after.
        Determine tier by reversibility x blast radius (file count is only a weak hint).
      </step>
      <step id="handoff">
        Output structured diagnosis.
        Hand off to /kernel:ingest with pre-identified scope.
      </step>
    </steps>
  </mode>
</modes>

<output_format>
## Diagnosis: {title}

**Mode:** bug | refactor
**Root cause:** {one sentence}
**Confidence:** high | medium | low

### Affected Files
| File | Role |
|------|------|
| {path} | origin — where the bug lives / refactor starts |
| {path} | downstream — affected by the change |

### Blast Radius
{N} files affected. **Tier {1|2|3}.**

### Hypotheses Tested (bug mode)
1. "{hypothesis}" → CONFIRMED | REJECTED ({evidence})

### Dependency Map (refactor mode)
{what depends on what}

### Recommended Approach
{what to do, not how — that's for ingest/forge}

### Tests Required
- {test that must pass before the fix}
- {test that validates the fix}

---
**Next:** /kernel:ingest or /kernel:forge to implement.
</output_format>

<telemetry>
Record diagnosis event:
  agentdb emit command "diagnose" "" '{"mode":"bug|refactor","confidence":"high|medium|low","blast_radius":N,"tier":N}'
</telemetry>

</skill>
