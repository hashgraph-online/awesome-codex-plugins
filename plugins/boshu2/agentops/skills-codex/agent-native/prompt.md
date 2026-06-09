# agent-native

Make an out-of-session agent (Managed Agent / Agent SDK / sandbox loop) AgentOps-native via skills + the `ao` CLI + CI — not hooks.

## Instructions

Load and follow the skill instructions from the sibling `SKILL.md` file for this skill. Apply the hookless reframe: bundle AgentOps skills into the agent definition, expose `ao` as a callable tool (or shell it directly for Codex) so the loop self-bootstraps + self-validates, and gate every output through the SAME CI as interactive work. This is NOT a hook revival; no skill fork; Managed Agents are NOT ZDR (no holdout/PII in the definition); CI is the enforcement boundary.
