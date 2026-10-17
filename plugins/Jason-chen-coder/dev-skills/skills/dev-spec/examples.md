# Dev Spec Compatibility Examples

## Full skill set installed

User: "dev-spec --quick：当前用户导出自己的订单，CSV，字段沿用已确认白名单；生成 spec 就好。"

Load installed `dev-grill-docs` with `--quick --spec-only`. Inspect the existing whitelist and related behavior. If no material gap remains, write `.claude/artifacts/designs/<feature>.md` without forcing a question. Preserve the user's spec-only boundary: no glossary, ADR, or implementation.

## Standalone installation

Only `dev-spec` is installed. The user asks for a feature specification.

Read the bundled baseline and use the standalone compatibility contract in `SKILL.md`. Produce the same artifact, scope fields, AC identifiers, and lifecycle statuses. Do not fail because a sibling `dev-grill-docs` directory is absent.

## Unresolved field policy

The export format is known, but the requested personal-data fields have no accepted policy or repository definition.

Ask for the material field decision or mark that scope `STUCK` with the exact blocker. Stable entity names and a completed format discussion do not make the sensitive field contract ready. Do not label it `ALIGNED` merely because several interview rounds have elapsed.

## Chat-only request

User: "用 dev-spec 梳理一下范围，先只在对话里说，不写文件。"

Return the scope and any material question in chat. The default artifact path does not override the explicit no-file instruction.
