# SkillBundle Interchange Format

The SkillBundle is the universal intermediate representation produced by the converter's parse stage. Every target adapter consumes a SkillBundle and transforms it into platform-specific output.

## Schema

```yaml
SkillBundle:
  name: string          # from frontmatter 'name' field
  description: string   # from frontmatter 'description' field
  body: string          # markdown content after frontmatter (closing --- to EOF)
  references:           # files found in references/ directory
    - name: string      # filename (e.g. 'output-format.md')
      content: string   # full file content
  scripts:              # files found in scripts/ directory
    - name: string      # filename (e.g. 'validate.sh')
      content: string   # full file content
  frontmatter: object   # full parsed YAML frontmatter as key-value pairs
```

## Field Details

### name (string, required)

The skill's short name, extracted from the `name` field in SKILL.md YAML frontmatter.

Example: `council`, `validate`, `plan`

### description (string, required)

The skill's description, extracted from the `description` field in SKILL.md frontmatter. May contain trigger lists and usage summaries.

### body (string, required)

The full markdown content of SKILL.md after the closing `---` of the frontmatter block. This is the skill's instructions, workflow documentation, and inline agent definitions.

### references (array of objects)

Each file in the skill's `references/` directory becomes one entry:

- **name**: The filename without path prefix (e.g. `output-format.md`)
- **content**: The complete file contents as a string

If no `references/` directory exists, this is an empty array.

### scripts (array of objects)

Each file in the skill's `scripts/` directory becomes one entry:

- **name**: The filename without path prefix (e.g. `validate.sh`)
- **content**: The complete file contents as a string

If no `scripts/` directory exists, this is an empty array.

### frontmatter (object)

The complete parsed YAML frontmatter as a flat or nested key-value structure. This includes all fields -- not just `name` and `description` -- so target adapters can access `metadata.tier`, `metadata.dependencies`, and any custom fields.

Example:

```yaml
frontmatter:
  name: council
  description: 'Multi-model consensus council...'
  metadata:
    tier: orchestration
    dependencies:
      - standards
    replaces: judge
```

## Usage in Target Adapters

Target adapters receive the SkillBundle and decide which fields to use:

| Adapter | Fields Used | Notes |
|---------|-------------|-------|
| codex | name, description, body, references | Flattens into single agents.md |
| cursor | name, description, body, references | Splits into .cursor/rules/ files |
| test | all | Dumps full bundle for inspection |

## Serialization

The SkillBundle is an in-memory structure passed between pipeline stages. When written to disk (e.g. by the `test` target), it is rendered as structured markdown with clear section headers for each field.
