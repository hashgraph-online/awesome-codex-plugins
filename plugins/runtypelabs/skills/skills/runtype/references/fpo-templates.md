# FPO Templates

FPO Templates are Runtype's **distribution format**. A template wraps a `FullProductObject` with import-time variables that get substituted on import, producing a ready-to-run product.

Use templates when you want to ship a Runtype product to someone else's workspace — internal team distribution, customer-shippable starters, marketplace listings.
Prefer live `runtype://types/fpo-template` and `runtype://types/fpo` when available.

## Contents

- [The TypeScript shape](#the-typescript-shape)
- [How import works](#how-import-works)
- [Validity](#validity)
- [Secrets: the right pattern](#secrets-the-right-pattern)
- [Template variables — when to use them](#template-variables--when-to-use-them)
- [Authoring workflow](#authoring-workflow)
- [Validation tools](#validation-tools)
- [Anti-patterns](#anti-patterns)
- [Why this format exists](#why-this-format-exists)

## The TypeScript shape

```ts
export interface FullProductObjectTemplate {
  version: '1.0' | '1.1'
  /** A FullProductObject — see runtype://types/fpo */
  productObject: object
  template: {
    variables: FpoTemplateVariable[]
  }
}

export interface FpoTemplateVariable {
  key: string
  label: string
  description?: string
  inputType: 'text' | 'textarea' | 'url' | 'secret' | 'select' | 'number' | 'boolean'
  required: boolean
  defaultValue?: string | number | boolean
  placeholder?: string
  options?: { label: string; value: string | number | boolean }[]
}
```

The template wrapper version is separate from `productObject.version`. New product
objects should normally use FPO `version: "2.0"`, whose inline agents put runtime
fields under `agent.config`. Use `"1.0"` / `"1.1"` product objects only when editing
legacy flat-agent templates.

## How import works

1. User opens the template in the Runtype UI (or via MCP `import_*` flow).
2. The platform shows a form generated from `template.variables`.
3. User fills in the values.
4. The platform substitutes `{{key}}` references in `productObject` with the user-supplied values.
5. The result is validated as a `FullProductObject` and materialized — product, agents, flows, tools, surfaces, schedules, all created in the user's workspace.

## Validity

A template is valid if it declares **at least one of**:

- A template variable (something the importer fills in), or
- A tool with `auth.setupRequired: true` and a non-empty `auth.secrets` array.

The second condition exists so a template can declare "pending secrets" without requiring any plain-text variables at import.

## Secrets: the right pattern

There are two ways to handle secrets in templates, and one is much better than the other.

### Bad: template variable with `inputType: 'secret'`

```json
{
  "template": {
    "variables": [
      { "key": "OPENAI_KEY", "label": "OpenAI API Key", "inputType": "secret", "required": true }
    ]
  }
}
```

This renders a password input — but the supplied value is substituted **literally** into the resolved product object. The secret ends up in the DB product record. Not a credential-safe path.

### Good: pending-secret pattern

Declare the secret on the target tool's `auth.secrets` array in the wrapped `productObject`. Reference it inside tool config with `{{secret:KEY}}` — singular `secret`, colon, UPPER_CASE. Same syntax everywhere: tool config (runtime) and FPO templates use the same form. `{{secrets:KEY}}` (plural with colon) is invalid; `{{secrets.key}}` (plural with dot) is a different system for per-request dispatch-scoped values, not managed secrets.

```json
{
  "productObject": {
    "tools": [
      {
        "name": "openai_chat",
        "auth": {
          "setupRequired": true,
          "secrets": [
            {
              "key": "OPENAI_KEY",
              "label": "OpenAI API Key",
              "description": "Your OpenAI org's API key"
            }
          ]
        },
        "config": {
          "headers": { "Authorization": "Bearer {{secret:OPENAI_KEY}}" }
        }
      }
    ]
  },
  "template": { "variables": [] }
}
```

On import:

- Platform sees `setupRequired: true` and the `auth.secrets` declaration.
- It creates placeholder secret bindings with `status: 'needs_configuration'`.
- It prompts the user to fill them via the intake flow.
- Once filled, the secret value lives in the secret store — **never in the product record**.

This is the pattern to use for every credential.

## Template variables — when to use them

Use `template.variables` for things that are **not credentials**:

- Configuration URLs (webhook destinations, base API URLs)
- Recipient lists (default email recipients, default Slack channel)
- Model preferences (which model to use — surface as a `select` with options)
- Display names, branding strings
- Numeric thresholds (max retries, timeout in seconds)

Substitution happens at import time via `{{key}}`. Use these in any text field in the wrapped `productObject`.

## Authoring workflow

1. Build the product normally in Runtype (via MCP or UI).
2. Test it end-to-end.
3. Identify what the next user would need to change:
   - Credentials → pending-secret pattern.
   - Other config → `template.variables`.
4. Export the product as an FPO Template (the platform has tools for this, or you can assemble it by hand from `get_product`).
5. Validate: `validate_product` on the resolved object (substitute test values for variables), `validate_product_tool` / `validate_product_flow` for sub-parts.
6. Ship the JSON.

## Validation tools

| Tool                       | Purpose                                       |
| -------------------------- | --------------------------------------------- |
| `validate_product`         | Full product object — run before distributing |
| `validate_product_tool`    | A tool definition inside the FPO              |
| `validate_product_flow`    | A flow definition                             |
| `validate_product_agent`   | An agent definition                           |
| `validate_product_surface` | A surface definition                          |

These catch schema problems before the template lands in someone else's workspace.

## Anti-patterns

- **Hardcoded credentials** in `productObject` (even temporarily). Use the pending-secret pattern.
- **Too many template variables**. Each variable is a question the user has to answer. Cap at ~5; for more config, use sensible defaults and let the user tweak post-import.
- **Variables referring to platform internals** (workspace ids, surface keys). The platform assigns these; don't try to template them.
- **Forgetting `setupRequired: true`** when declaring pending secrets. Without it, the intake flow won't trigger.

## Why this format exists

The FPO Template format is what makes Runtype products **portable**. Without it, distributing a product means a setup doc and a series of MCP/UI steps. With it, distributing a product is one file and an import button. This is the model: treat each Runtype product as a unit that can be authored once, shipped many times, and re-configured per environment.
