# Upstream Notice

Shout out to `epoko77-ai/im-not-ai`: this skill adapts selected Korean AI-tell ideas from that project.

- Source repository: https://github.com/epoko77-ai/im-not-ai
- Source license: MIT, copyright 2026 epoko77-ai
- Adaptation boundary: Superloopy packages local references instead of the upstream Codex symlink, adds a dependency-free audit script, adds Superloopy evidence output, and maintains its own quality rubric.
- Last idea sync: upstream v2.4 (commit `0ac1e84`, 2026-08-23). Adapted: modality preservation (서법 보존) as a contract rule plus a P5-style deontic/hedge marker-count warning in the audit; D-6 retargeted to deontic paragraph endings with a reposition-only repair (upstream I-4); C-8 paired-antithesis rule at the lowered 2+ threshold. Not adapted: upstream A-16 (pronoun repetition) — it fires only in translation contexts and this skill has no translation mode.

Include the upstream MIT copyright notice in release notes or distribution artifacts when substantial upstream text is copied.
