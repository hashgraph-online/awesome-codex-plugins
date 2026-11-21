# Delegated work

Conditional detail for [Implement](../SKILL.md): read it when delegation is
authorized and useful, or when the caller asks for a one-shot adapter or a
factory. Current-session execution remains the default.

## Lanes

Keep concurrent writers disjoint and isolated as
[Orchestrate](../../orchestrate/SKILL.md#check-the-packets) describes; shared generators and
integration serialize. Supply each lane its intent, acceptance, scope and
review owner, then integrate its exact content and check facts, carrying its
`not_as_briefed` and `gaps` lines into yours. A selected wave ends with the
caller-requested wave result; do not invent another wave. One fresh review of
the integrated candidate can cover unjudged increments; when the integrator
owns that review, workers return their handoff without commissioning another.
Preserve any separately required lane judgments; a successful process exit is
not semantic PASS.

## One-shot adapters and factories

When the caller asks for a one-shot adapter (a script or command that sends
supplied operations to a tool or runtime), it dispatches each operation once,
reports its output or error and stops, with no scheduler, retry controller or
store; show its dispatch count and failure reporting with a dry-run or fixture.
A factory, an external multi-agent system with its own coordinator such as Gas
City, runs only when the caller selects it.
