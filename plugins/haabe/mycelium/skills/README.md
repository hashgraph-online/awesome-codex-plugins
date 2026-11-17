# Skills — 44 Reusable Agent Operations

Skills are composable operations the agent can perform. Each skill is a structured prompt with a defined workflow, inputs, outputs, and theory citations. They are invoked with `/skill-name` (e.g., `/interview`, `/threat-model`, `/dora-check`).

Every skill lives in its own directory with a `SKILL.md` file that defines the complete workflow.

## Skills by Phase

### Getting Started
| Skill | What It Does |
|-------|-------------|
| `/interview` | Structured product discovery interview — the entry point for new projects |
| `/diamond-assess` | Evaluate current diamond state and recommend next action |
| `/diamond-progress` | Progress a diamond through phases with full gate validation |

### Discovery (L0-L2)
| Skill | What It Does |
|-------|-------------|
| `/jtbd-map` | Map Jobs to Be Done (Christensen) |
| `/user-interview` | Conduct a user interview with bias-aware question design |
| `/user-needs-map` | Map user needs (Allen) |
| `/ost-builder` | Build an Opportunity Solution Tree (Torres) |
| `/wardley-map` | Create or update a Wardley Map for strategic landscape |
| `/cynefin-classify` | Classify problem domain using Cynefin (Snowden) |
| `/mocked-persona-interview` | Test assumptions with a simulated persona interview |
| `/handoff` | Generate structured materials for offline human tasks |

### Solution Design (L3)
| Skill | What It Does |
|-------|-------------|
| `/gist-plan` | Create a GIST plan (Goals, Ideas, Steps, Tasks) |
| `/ice-score` | Score solutions using ICE (Impact, Confidence, Ease) |
| `/assumption-test` | Design and run lightweight assumption tests |
| `/service-check` | Evaluate against Downe's 15 Good Services principles |
| `/usability-check` | Evaluate against Nielsen's 10 usability heuristics |

### Delivery (L4)
| Skill | What It Does |
|-------|-------------|
| `/delivery-bootstrap` | Bootstrap a delivery diamond with JiT tooling |
| `/preflight` | Pre-task safety check (corrections, secrets, scope) |
| `/reflexion` | Implement → validate → self-critique → retry loop |
| `/definition-of-done` | Executable DoD checklist for delivery completion |
| `/dora-check` | Measure DORA metrics (deployment frequency, lead time, CFR, MTTR) |
| `/threat-model` | STRIDE-based threat modeling |
| `/security-review` | Security review against OWASP top 10 |
| `/privacy-check` | Privacy assessment (GDPR/Privacy by Design) |
| `/a11y-check` | Accessibility audit |

### Market (L5)
| Skill | What It Does |
|-------|-------------|
| `/launch-tier` | Classify launch tier and readiness |
| `/metrics-detect` | Auto-detect available metric sources |
| `/metrics-pull` | Pull and normalize metrics from all configured sources |

### Health and Quality (Cross-Cutting)
| Skill | What It Does |
|-------|-------------|
| `/bvssh-check` | Better/Value/Sooner/Safer/Happier assessment (Smart) |
| `/bias-check` | Pre-research and pre-decision bias review |
| `/devils-advocate` | Challenge assumptions and play devil's advocate |
| `/feedback-review` | Health check across all feedback loops |
| `/canvas-health` | Lint canvas for missing fields, stale confidence, orphaned refs |
| `/canvas-sync` | Sync canvas between repos |
| `/canvas-update` | Update a canvas file with new evidence |
| `/log-evidence` | Log evidence from human tasks back into canvas |
| `/corrections-audit` | Audit corrections.md for recurring patterns |
| `/friction-log` | Draft a short account of where USING Mycelium was confusing, for the user to edit and choose whether to send (Hoskins) |
| `/retrospective` | Structured retrospective after delivery |
| `/regulatory-review` | EU AI Act and regulatory compliance check |
| `/team-shape` | Assess team topology (Skelton & Pais) |

### Framework Operations
| Skill | What It Does |
|-------|-------------|
| `/framework-health` | Quarterly framework self-assessment |
| `/eval-runner` | Run evaluation scenarios against the framework |
| `/fan-out` | Parallel exploration with worktree-isolated agents |
| `/prompt-optimizer` | A/B test and optimize framework prompts |

## Skill Anatomy

Every `SKILL.md` follows this structure:

1. **When to Use** — conditions that trigger the skill
2. **Workflow** — numbered steps the agent follows
3. **Output** — what gets written and where
4. **Theory Citations** — which frameworks inform the skill

Skills are suggested contextually by `/diamond-assess` and `/diamond-progress` at each decision, and by hooks when relevant conditions are detected.
