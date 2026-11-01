---
name: motion-video-recreation
description: "Recreate reference motion videos through HyperFrames v2, Motion IR, deterministic export, and source-to-output visual review."
user-invocable: true
when_to_use: "Use for analyzing and recreating a UI/product promo from a reference video, from source frames through reviewed final export."
category: frontend
keywords: [video-recreation, motion-design, promo-video, hyperframes, motion-ir, virtual-clock, ffmpeg]
license: PolyForm Shield 1.0.0 (see LICENSE)
metadata:
  author: design-os
  version: "2.1.0"
---

# Motion Video Recreation (v2)

**Read [the normative pipeline contract](../../docs/pipelines/motion-video-recreation-pipeline.md) before work.** It defines intake, scene/transition ledger, stage exits, hard fails, verification, acceptance, and cross-session handoff. [Lessons from Astra](../../docs/pipelines/motion-video-recreation-workflow-guide.md) explain the failure modes. Do not use a numeric parity promise or treat technical gates as visual acceptance.

## Mandatory preconditions

1. Read `AGENTS.md`, the active case plan, and `skills/product-designer/SKILL.md`. Activate/consult Product Designer before creating, modifying, or auditing scenes, UI or animation. Check the current worktree and preserve existing changes.
2. Identify the source video, native metadata, frame-index evidence, deliverable format, rights boundary, and current encoded artifact. If the source is unavailable, mark visual comparison unverified.
3. Record the owner's decisions on asset substitutions, scope, review and publication. Do not silently override them.

## Execute the contract

1. **Deconstruct:** use `scripts/detect-scene-cuts.mjs` and `scripts/extract-audio-waveform.mjs` as aids, then manually map every state and soft transition. Create source-indexed scene and boundary records per the contract.
2. **Stage:** map states to supported HyperFrames beats in `src/runtime/hyperframes-engine.mjs`, build a finite paused draft, and sample `src/runtime/hyperframes-motion-presets.mjs` for each declared timing track. Record reference-specific exceptions.
3. **Implement:** specify vector intent through `schemas/motion-ir.schema.json` and deterministic geometry. Use one seekable virtual clock. Keep scene/world camera separate from overlays and preserve reduced-motion content.
4. **Review:** compare the reference and current browser proof at exact frames, including dense boundary strips and continuous playback. Use an independent reviewer for material visual gaps and verify every finding against source.
5. **Export and close:** export after the last edit, inspect the encoded MP4 at full size and in motion, run relevant technical gates, and report one acceptance state from the contract. Leave a complete case handoff.

## Non-negotiable boundaries

- HyperFrames v2 is a required staging and timing system, not a decorative import. Source-specific choreography may refine its presets.
- No LLM-generated raw SVG path animation; Motion IR plus deterministic geometry tooling own paths and morphs.
- Prefer composited transforms/opacity; document and verify any layout-animation exception needed for sharp source fidelity.
- Official icon libraries, sourced SVGL marks, reduced-motion fallback, finite timelines and the repository anti-flop gates remain mandatory.
- A passing export, test suite, pixel score or worker report cannot establish visual similarity. The final encoded artifact and owner acceptance decide that claim.
