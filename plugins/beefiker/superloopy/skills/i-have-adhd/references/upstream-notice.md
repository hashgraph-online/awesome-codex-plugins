# Upstream Notice

This skill adapts `ayghri/i-have-adhd`.

- Source repository: https://github.com/ayghri/i-have-adhd
- Reviewed revision: `b42a45a068e080294924bfba19a7a2e8944c48ff` (2026-08-24 review; previously `07684c4ab625dd7d1ea6e99e065f60bc0ac6a1ba`)
- Review outcome: no rule-content changes since the prior revision — the ten-rule output contract is unchanged. Upstream changes were host packaging (installers, hooks, editor integrations), a frontmatter metadata flattening for strict parsers, and `allow_implicit_invocation` flipped to `false`, which this adaptation already enforced.
- Source license: MIT, copyright 2026 Ayoub Ghriss
- Adaptation boundary: Superloopy preserves the ten-rule output contract, disables host-level implicit activation, adds a non-diagnostic loop-only cue boundary, and keeps Superloopy safety and evidence gates authoritative.

The full upstream MIT notice is packaged in `../LICENSE`.
