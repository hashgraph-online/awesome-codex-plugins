# Upstream Notice

Shout out to `epoko77-ai/im-not-ai`: this skill adapts selected Korean AI-tell ideas from that project.

- Source repository: https://github.com/epoko77-ai/im-not-ai
- Source license: MIT, copyright 2026 epoko77-ai
- Adaptation boundary: Superloopy packages local references instead of the upstream Codex symlink, adds a dependency-free audit script, adds Superloopy evidence output, and maintains its own quality rubric.
- Last idea sync: upstream v2.7 taxonomy (commit `9747f03`, 2026-09-06; upstream tags no release for rule changes, so the sync is commit-based — run `node scripts/upstream-drift.mjs` to measure drift). Adapted 2026-09-10: C-8 base-rate correction (31 of 532 human documents) and injection ban; A-1/A-10/A-11 flipped to default-preserve, density-triggered; generic injection guard in the audit; A-21, D-8, D-9, D-10, D-12 as counted S2 rules; A-20, A-22, A-24 as advisory counters; A-16 (antecedent-count condition), A-23, D-11, F-7, I-7, and the rhetorical-quote policy as guidance only; chatbot-frame hygiene as local Q-1; false-positive principles in the quality rubric. Not adapted: D-13 (essay-only, no essay genre here), D-14 metaphor-family sum (judgment, no counter), restore_modality/P5 pairwise restorer and strip_injected_commas (our count-based modality warning and C-11 counter stay), calibration corpora and the corruption engine (no corpus here). Superloopy's own measurement (P family: adverb calques such as 조용히; metaphor idioms are NOT calqued into Korean) has no upstream counterpart and stays local by J's decision.
- Previous sync: upstream v2.4 (commit `0ac1e84`, 2026-08-23). Adapted: modality preservation (서법 보존) as a contract rule plus a P5-style deontic/hedge marker-count warning in the audit; D-6 retargeted to deontic paragraph endings with a reposition-only repair (upstream I-4); C-8 paired-antithesis rule at the lowered 2+ threshold. Not adapted: upstream A-16 (pronoun repetition) — it fires only in translation contexts and this skill has no translation mode.

- Local additions with no upstream counterpart: K-1, M-1, N-1, and the P calque family (조용히, 우아하게, 투명하게, 단일 진실 공급원, 정본, 안전하게 실패; 2026-09-10, measured in `docs/specs/2026-09-10-korean-calque-rules-design.md`). P ids stay local until upstream adopts an A-17+ equivalent; alias them here when it does.

Include the upstream MIT copyright notice in release notes or distribution artifacts when substantial upstream text is copied.
