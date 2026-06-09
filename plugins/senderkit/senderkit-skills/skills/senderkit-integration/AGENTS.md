# SenderKit Integration Skill

This directory contains a portable, open-source agent skill for integrating SenderKit into applications. The canonical source is `https://github.com/senderkit/senderkit-skills`, and this reusable skill lives in the repository's `skills/senderkit-integration/` directory.

For any coding assistant or LLM:

1. Read `SKILL.md` first.
2. Follow the workflow in order.
3. Load reference files only when relevant:
   - `references/language-detection.md`
   - `references/api-reference.md`
   - `references/examples.md`
   - `references/migration-playbook.md`
   - `references/verification.md`
4. Fetch the current SenderKit OpenAPI spec before writing REST request shapes:
   - `https://www.senderkit.com/openapi.yaml`
5. Use `scripts/fetch_openapi.py` when a local sync or drift check is needed.

Do not treat bundled reference notes as a frozen API specification. The published OpenAPI document is the source of truth.
