# Full Skill Catalog

Pick what you need. Every skill works standalone. `$swarm` multiplies any of them.

## Composition Map — What Calls What

```
$evolve ──► $rpi (per fitness gap, loops until goals met)
    │
    ▼
$rpi ──► $research → $plan → $pre-mortem → $crank → $vibe → $post-mortem
    │
    ▼
$crank ──► $swarm ──► $implement (×N per wave, fresh context each)
    │
    ▼
$swarm ──► parallelize anything: research, brainstorm, implement, council
    │
    ▼
┌─────────────────────────────────────────────────┐
│               STANDALONE PRIMITIVES             │
│                                                 │
│  $research ─────► may trigger $brainstorm       │
│  $brainstorm ───► may spawn $swarm              │
│  $plan ─────────► may call $pre-mortem          │
│  $implement ────► research + plan + build + vibe│
│  $vibe ─────────► $complexity + $council        │
│  $pre-mortem ───► $council (failure simulation) │
│  $post-mortem ──► $council + knowledge lifecycle│
│  $council ──────► parallel judges (multi-model) │
└─────────────────────────────────────────────────┘
```

## Skills by Category

```
THE MULTIPLIER                   VALIDATE
$swarm      - parallelize        $vibe        - code quality check
              anything           $pre-mortem  - plan validation
                                 $post-mortem - full retro + knowledge lifecycle
BUILD                            $council     - multi-model judges
$implement  - single task        $release     - tag + changelog
$crank      - multi-issue epic
$plan       - decompose work     KNOWLEDGE
$rpi        - full lifecycle     $knowledge   - query learnings
                                 $post-mortem --quick - quick-capture
EXPLORE                          $post-mortem - full retro + knowledge
$research   - deep dive          $trace       - decision provenance
$brainstorm - explore ideas      $flywheel    - health monitoring
$bug-hunt   - investigate
$complexity - code metrics       SESSION
$doc        - docs, README       $handoff     - save + resume
              (--mode=readme),    $recover     - restore after compaction
              OSS pack            $status      - dashboard
              (--mode=oss)
PRODUCT
$product    - define mission     CONTRIBUTE (upstream PRs)
$goals      - fitness specs      $pr-research, $plan, $pr-implement
$evolve     - goal-driven loop   $validate --mode=pr, $pr-prep
                                 (PR learnings: $post-mortem --scope=pr)
META
$quickstart - onboarding         CROSS-VENDOR
$converter  - export to Codex,   $swarm       - parallel Codex agents
              Cursor             $openai-docs - OpenAI docs lookup
```
