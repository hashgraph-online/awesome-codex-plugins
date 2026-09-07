---
name: architecture
description: "System architecture and design patterns. Modular design, interface stability, dependency management, AI-code health nexus. Triggers: architecture, design, structure, modules, dependencies, coupling, system design."
allowed-tools: Read, Grep, Glob, Task
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="architecture">

<purpose>
Architecture is about managing change over time.
Good architecture makes easy things easy and hard things possible.
AI-generated code amplifies existing patterns—good or bad.
</purpose>

<prerequisite>
Understand existing codebase structure before proposing changes.
Check for established patterns. Follow them unless explicitly changing.
</prerequisite>

<reference>
Skill-specific: skills/architecture/reference/architecture-research.md
</reference>

<core_principles>
1. FOLLOW EXISTING PATTERNS: Don't introduce new patterns without justification.
2. INTERFACE STABILITY: Changing interfaces breaks everything. Stabilize them first.
3. MODULAR BOUNDARIES: Clear separation. Each module has one reason to change.
4. DEPENDENCY DIRECTION: Depend on abstractions, not concretions. Core doesn't know about edges.
5. SMALLEST CHANGE: Prefer minimal changes that achieve the goal.
</core_principles>

<ai_code_health_nexus>
From research: 30%+ defect risk when AI applied to unhealthy code.
AI amplifies existing patterns. If code is messy, AI makes it messier.
Before adding AI to a codebase:
1. Identify health score (coupling, complexity, test coverage)
2. Fix critical health issues first
3. Establish clear interfaces
4. Then apply AI within those boundaries
</ai_code_health_nexus>

<design_heuristics>
- If you can't explain it simply, the design is too complex
- Three concrete examples before abstraction
- Composition over inheritance
- Make illegal states unrepresentable
- Parse, don't validate
</design_heuristics>

<anti_patterns>
- Premature abstraction (abstract before 3 concrete uses)
- Leaky abstractions (implementation details bleeding through)
- Circular dependencies
- God objects (one class doing everything)
- Feature envy (methods that use another class more than their own)
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"architecture","decision":"X","coupling_reduced":true,"adr":"path|none"}'
</on_complete>

</skill>
