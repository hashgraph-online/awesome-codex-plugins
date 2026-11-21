# Status block

[Orchestrate](../SKILL.md) returns this shape when the caller asks for
coordination status. No other report or persisted artifact is required unless
an existing consumer needs one.

```text
assignments: <worker/context id> -> <task>, state as observed (how); last activity <time, kind> | unobserved
candidates:  <task> -> <exact ref>; checks <result>; judgment <ref | owed | not owed>
next:        <free capacity> -> <dispatch>, because <observed bottleneck>
held:        <task>, blocked by <prerequisite gap | not_as_briefed step | out of authority action>
handoffs:    <affected work updated, and where>
gaps:        <unobserved state, unknown identities, unresolved dissent>
```
