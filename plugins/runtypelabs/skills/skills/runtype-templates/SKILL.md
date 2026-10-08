---
name: runtype-templates
description: 'Create, validate, or share distributable Runtype Full Product Object (FPO) templates with import-time variables and pending secrets, or install a product from a runtype.com example, a use.runtype.com/now link, or a template URL.'
user-invocable: true
argument-hint: '[FPO or template task]'
---

# Runtype Templates

Use this skill when a Runtype product should become a portable Full Product Object (FPO)
template that another workspace, team, customer, or marketplace user can import. It also
covers installing a product from a shared example or template link.

## Source of truth

When the Runtype MCP server is available, read the schema docs before you write or
validate a template.

Always read:

- `get_platform_documentation(topic="types-fpo-template")` for the template wrapper.
- `get_platform_documentation(topic="types-fpo")` for the wrapped `productObject`. Use
  FPO version `2.0` for new templates.
- `get_platform_documentation(topic="product-schema")` for the JSON Schema of the
  product object.

Read these when the template contains that part:

- Surfaces: `surface-types` and `types-surface-configs`.
- Flows: `flow-step-types`.
- Tools: `builtin-tools`, `orthogonal-tools`, and `external-tools`.

For prose guidance, call `search_documentation` for "FPO templates" or read the public
guides: [FPO templates](https://docs.runtype.com/developer-guides/guides/fpo-templates) and
[Importing products](https://docs.runtype.com/developer-guides/guides/importing-products).

## Template shape

An FPO template has three top-level keys:

- `version`: the template format version, `"1.0"` or `"1.1"`. This is separate from
  `productObject.version`, which is `"2.0"` for new templates.
- `productObject`: the full product definition.
- `template.variables`: the non-secret values the importer supplies.

A template must declare at least one variable, or at least one tool with
`auth.setupRequired: true` and a non-empty `auth.secrets` array.

Use variables for names, public URLs, recipient lists, selected models, and other
non-secret configuration. Every credential uses the pending-secret pattern.

### Variables

Each variable needs `key`, `label`, `inputType`, and `required`:

```json
{
  "key": "companyName",
  "label": "Company name",
  "inputType": "text",
  "required": true,
  "defaultValue": "Acme"
}
```

- `inputType` is one of `text`, `textarea`, `url`, `secret`, `select`, `number`, or
  `boolean`.
- A `select` variable needs a non-empty `options` array of `{ "label", "value" }`. Only
  `select` variables can have `options`.
- A template can declare up to 50 variables.
- Set defaults with `defaultValue`. Inline `{{key|default}}` syntax is rejected.
- When a string field is exactly `{{key}}` and the variable is `number` or `boolean`, the
  field keeps that type. Every other substitution produces a string.

### Runtime tokens and template variables

Import treats every bare `{{name}}` in `productObject` as a template variable. That
includes runtime tokens such as a step output in a prompt. Only these references pass
through to run time without a declaration:

- `{{secret:KEY}}`
- `{{flow:name}}`, which resolves to the flow variable `name` at run time
- System and message variables, such as `{{_record.metadata.field}}`, `{{_now}}`,
  `{{userMessage}}`, and `{{messages}}`

When you turn a working product into a template, rewrite runtime flow tokens with the
`flow:` prefix. For example, change `Summarize {{research}}` to
`Summarize {{flow:research}}`. Do not declare a runtime token as a template variable,
because import replaces it with a fixed value.

If a field cannot take the `flow:` prefix, such as a Liquid template body, declare a
template variable whose `defaultValue` is the runtime text, and reference that variable in
the field.

### Optional bundled resources

A template can also ship these `productObject` arrays. Import creates each resource:

- `schedules[]`: cron or one-time runs that target a capability through `capabilityId`.
  A scheduled capability does not need a `type: "schedule"` surface.
- `evals[]`: eval suites with their cases.
- `skills[]`: agent skills, bound to agent capabilities through `bindTo`.

For the field tables, see the FPO templates guide.

## Pending secrets

Use this pattern for every credential:

1. Declare the key on the target tool's `auth.secrets` array.
2. Set `auth.setupRequired: true`, plus `auth.type` and `auth.setupInstructions`.
3. Reference the key in the tool config as `{{secret:KEY}}`.
4. Leave the value out of the template. Import creates the secret as unconfigured, and the
   importer fills it in after import.

```json
{
  "config": {
    "headers": { "Authorization": "Bearer {{secret:ACME_API_KEY}}" }
  },
  "auth": {
    "type": "api_key",
    "setupRequired": true,
    "secrets": [{ "key": "ACME_API_KEY", "required": true }],
    "setupInstructions": {
      "summary": "Add your Acme API key.",
      "steps": ["Create an API key in Acme.", "Add it as a secret after import."]
    }
  }
}
```

Each `auth.secrets` entry is an object with `key` and `required`, not a bare string.

Do not use a variable with `inputType: "secret"` for credentials. Import writes that value
into the product object as plain text. A `secret` variable cannot have a `defaultValue`.

## Validation workflow

1. Validate the template document with `runtype validate-product ./template.json --template`
   or `POST https://api.runtype.com/v1/public/products/validate-template`. Fix every error,
   such as `UNDECLARED_TEMPLATE_VARIABLE`, `INLINE_TEMPLATE_DEFAULT_NOT_ALLOWED`, and
   `DUPLICATE_TEMPLATE_VARIABLE`. Review warnings such as `UNUSED_TEMPLATE_VARIABLE` and
   `TEMPLATE_VARIABLE_SECRET_IS_UNSAFE`.
2. Resolve template defaults, or supply test values for required variables.
3. Run `validate_product` on the resolved product object.
4. Run the focused validators for changed parts: `validate_product_tool`,
   `validate_product_flow`, `validate_product_agent`, and `validate_product_surface`.
5. Confirm that every route references a real capability id.
6. Confirm that every secret reference has a matching pending-secret declaration.
7. Confirm that importer-visible variables are few and meaningful.

## Share a template

1. Host the template JSON at a public HTTPS URL, such as a raw GitHub file URL.
2. URL-encode that URL and share `https://use.runtype.com/now?from=ENCODED_TEMPLATE_URL`.
3. Optional: Prefill a variable with `&templateParam%3AVARIABLE_KEY=VALUE`. The import page
   ignores prefilled values for secret variables.
4. Optional: Add a button to a repository `README`:

   ```md
   [Deploy to Runtype](https://use.runtype.com/now?from=https%3A%2F%2Fexample.com%2FYOUR_TEMPLATE.json)
   ```

5. Test the link: pass it to `create_product_from_example` as `url` and confirm the product
   is created.

## Set up a product from a link

When a user provides a `use.runtype.com/now?...` link, a `runtype.com/examples/<slug>` page,
or a direct FPO or template JSON URL, do not open the dashboard page, which requires
sign-in. Pass the original link to `create_product_from_example` as `url`, or pass a known
`slug` from `list_example_templates`.

1. Supply import-time values in the tool's `variables` argument. Omitted keys fall back to
   `templateParam` values in the link, then to template defaults. If a required variable
   still has no value, the tool returns the variable specs and creates nothing. Ask the
   user for those values, then call the tool again with them in `variables`.
2. Draft examples require `allow_draft: true`. Use it only when the user intends to install
   that draft.
3. Call `get_product_setup` with the created product id. Complete the steps you can
   automate, and give the user the remaining secret, OAuth, or surface-install links. Never
   ask the user to paste secret values in chat. Give them the dashboard link from
   `get_product_setup` or `get_secret_intake_manifest`, then confirm with `check_secrets`.
4. Test the product at its user-facing layer. For an agent, call `execute_agent` with a
   `messages` array of `{ "role": "user", "content": "..." }` turns.

The tool rejects some links:

- A link with `?import=` or `?sessionId=` points to a temporary import preview. Ask for the
  original source: an example slug, a `?session=` link, or the document URL.
- A link with `?template=` points to a built-in dashboard template. Open it in the
  dashboard, or build the product with `create_product`.
- A `/now` link with none of `example`, `session`, `templateUrl`, or `from` has nothing to
  import. Ask the user for the full link.

## Anti-patterns

- Hardcoded API keys, tokens, client secrets, or bearer values.
- Too many variables. Every variable adds setup work for the importer.
- Workspace ids, runtime ids, or surface keys as template variables.
- Bare runtime tokens such as `{{research}}` left in the product object.
- Partial product schemas with a note that validation still needs work.
- Templates for one-off private account updates. Use the `runtype-admin` skill instead.

For platform scoping and account setup, use the `runtype` skill.
