---
name: runtype-templates
description: >-
  Use when creating, validating, exporting, importing, or improving Runtype Full Product
  Object templates. Covers FPO and FPO template structure, template variables, pending
  secrets, setup-required auth, validate_product and validate_product_* checks,
  distributable product packaging, import readiness, and avoiding credential leakage.
user-invocable: true
argument-hint: '[FPO or template task]'
---

# Runtype Templates

Use this skill when a Runtype product should become a portable artifact that another
workspace, team, customer, or marketplace user can import.

## Source Of Truth

When MCP is available, fetch current schema docs before writing or validating templates:

- `get_platform_documentation(topic="product-schema")`
- `get_platform_documentation(topic="types-fpo")`
- `get_platform_documentation(topic="surface-types")`
- `get_platform_documentation(topic="flow-step-types")`
- `get_platform_documentation(topic="builtin-tools")`
- `get_platform_documentation(topic="orthogonal-tools")`
- `get_platform_documentation(topic="external-tools")`
- Direct resource when available: `runtype://types/fpo-template`
- Direct resource when available: `runtype://types/surface-configs`

Prefer the live MCP docs over this skill's local fallback references.
For the template wrapper itself, read `runtype://types/fpo-template`; for the
wrapped `productObject`, read `types-fpo` because the current FPO default is
version `2.0`.

## Template Shape

An FPO template wraps a product object and import-time variables:

- `productObject`: the full product definition.
- `template.variables`: non-secret values the importer supplies.
- Tool `auth.setupRequired: true` plus `auth.secrets[]`: pending-secret declarations.

Template variables are for names, public URLs, recipient lists, selected models, and other
non-secret configuration. Credentials must use the pending-secret pattern.

## Pending Secrets

Use this pattern for every credential:

1. Declare the needed key on the target tool's `auth.secrets` array.
2. Set `auth.setupRequired: true`.
3. Reference the key in config as `{{secret:KEY}}`.
4. Leave the actual value out of the template.
5. Let the import/setup flow create `needs_configuration` secret bindings.

Do not use a `template.variables` entry with `inputType: "secret"` for credentials. That
substitutes the value into the resolved product object.

## Validation Workflow

1. Resolve template defaults, or supply test values for required variables.
2. Run `validate_product` on the resolved product object.
3. Run focused validators for changed parts: `validate_product_tool`,
   `validate_product_flow`, `validate_product_agent`, and `validate_product_surface`.
4. Confirm every route references a real capability id.
5. Confirm every secret reference has a matching pending-secret declaration.
6. Confirm importer-visible variables are few and meaningful.

## Anti-Patterns

- Hardcoded API keys, tokens, client secrets, or bearer values.
- Too many variables. Every variable is setup friction.
- Workspace ids, runtime ids, or surface keys as template variables.
- Partial product schemas with a note that validation still needs work.
- Using templates for one-off private account updates. Use `runtype-admin` instead.

If the umbrella `runtype` skill is installed alongside this focused skill, its durable
references provide deeper FPO template details. This skill must still work when
installed by itself; prefer live MCP docs over local sibling files.
