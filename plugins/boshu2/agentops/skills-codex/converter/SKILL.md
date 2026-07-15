---
name: converter
description: Convert AgentOps skill formats.
---
# Converter — Cross-Platform Skill Converter

Parse AgentOps skills into a universal SkillBundle format, then convert to target agent platforms.

## Constraints

- Treat the canonical source skill as read-only because conversion must not mutate the contract it is translating.
- Clean-write only the explicit target directory to prevent stale resources from surviving a conversion or unrelated paths from being deleted.
- Fail when copied-resource parity or target-format validation fails because a partial bundle is not a usable conversion.

## Pipeline

The converter runs a three-stage pipeline:

```
parse --> convert --> write
```

### Stage 1: Parse

Read the source skill directory and produce a SkillBundle:

- Extract YAML frontmatter from SKILL.md (between `---` markers)
- Collect the markdown body (everything after the closing `---`)
- Enumerate all files in `references/` and `scripts/`
- Assemble into a SkillBundle (see `references/skill-bundle-schema.md`)

### Stage 2: Convert

Transform the SkillBundle into the target platform's format:

| Target | Output Format | Status |
|--------|---------------|--------|
| `codex` | Codex SKILL.md + prompt.md | Implemented |
| `cursor` | Cursor .mdc rule + optional mcp.json | Implemented |

The Codex adapter produces a `SKILL.md` with YAML frontmatter (`name`, `description`) plus rewritten body content and a `prompt.md`. Default mode is **modular**: reference docs, scripts, and resources are copied as files and `SKILL.md` includes a local resource index instead of inlining everything. Optional **inline** mode preserves the older behavior by appending inlined references and script code blocks. Codex output normalizes foreign-runtime invocation syntax and paths, rewrites unsupported primitive labels to runtime-neutral wording, and preserves current flat `ao` CLI commands. It also deduplicates repeated runtime headings while preserving section content. Non-generated resource files and directories are copied with parity checks. Descriptions are truncated to 1024 characters at a word boundary if needed.

The Cursor adapter produces a `<name>.mdc` rule file with YAML frontmatter (`description`, `globs`, `alwaysApply: false`) and body content. References are inlined into the body, scripts are included as code blocks. Output is budget-fitted to 100KB max -- references are omitted largest-first if the total exceeds the limit. If the skill references MCP servers, a `mcp.json` stub is also generated.

### Stage 3: Write

Write the converted output to disk.

- **Default output directory:** `.agents/converter/<target>/<skill-name>/`
- **Write semantics:** Clean-write. The target directory is deleted before writing. No merge with existing content.

## CLI Usage

```bash
# Convert a single skill
bash skills/converter/scripts/convert.sh <skill-dir> <target> [output-dir]
bash skills/converter/scripts/convert.sh --codex-layout inline <skill-dir> codex [output-dir]

# Convert all skills
bash skills/converter/scripts/convert.sh --all <target> [output-dir]
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `skill-dir` | Yes (or `--all`) | Path to skill directory (e.g. `skills/council`) |
| `target` | Yes | Target platform: `codex`, `cursor`, or `test` |
| `output-dir` | No | Override output location. Default: `.agents/converter/<target>/<skill-name>/` |
| `--all` | No | Convert all skills in `skills/` directory |
| `--codex-layout` | No | Codex-only layout mode: `modular` (default) or `inline` (legacy inlined refs/scripts) |

## Supported Targets

- **codex** -- Convert to OpenAI Codex format (`SKILL.md` + `prompt.md`) with runtime-neutral rewrites and flat `ao` CLI preservation. Default is modular output with copied resources and a local-resource index; pass `--codex-layout inline` for legacy inlined refs/scripts. Missing copied resources fail fast.
- **cursor** -- Convert to Cursor rules format (`.mdc` rule file + optional `mcp.json`). Output: `<dir>/<name>.mdc` and optionally `<dir>/mcp.json`.
- **test** -- Emit the raw SkillBundle as structured markdown. Useful for debugging the parse stage.

## Extending

To add a new target platform:

1. Add a conversion function to `scripts/convert.sh` (pattern: `convert_<target>`)
2. Update the target table above
3. Add reference docs to `references/` if the target format needs documentation

## Examples

### Converting a single skill to Codex format

**Caller asks:** Convert `skills/council` to Codex format.

**What happens:**
1. The converter parses `skills/council/SKILL.md` frontmatter, markdown body, and any `references/` and `scripts/` files into a SkillBundle.
2. The Codex adapter transforms the bundle into a `SKILL.md` (body + inlined references + scripts as code blocks) and a `prompt.md` (Codex prompt referencing the skill).
3. Output is written to `.agents/converter/codex/council/`.

**Result:** A Codex-compatible skill package ready to use with OpenAI Codex CLI.

### Batch-converting all skills to Cursor rules

**Caller asks:** Convert all canonical skills to Cursor format.

**What happens:**
1. The converter scans every directory under `skills/` and parses each into a SkillBundle.
2. The Cursor adapter transforms each bundle into a `.mdc` rule file with YAML frontmatter and body content, budget-fitted to 100KB max. Skills referencing MCP servers also get a `mcp.json` stub.
3. Each skill's output is written to `.agents/converter/cursor/<skill-name>/`.

**Result:** All skills are available as Cursor rules, ready to drop into a `.cursor/rules/` directory.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `parse error: no frontmatter found` | SKILL.md is missing the `---` delimited YAML frontmatter block | Add frontmatter with at least `name:` and `description:` fields, or run Heal Skill on the source package first |
| Cursor `.mdc` output is missing references | Total bundle size exceeded the 100KB budget limit | The converter omits references largest-first to fit the budget. Split large reference files or move non-essential content to external docs |
| Output directory already has old files | Previous conversion artifacts remain | This is expected -- the converter clean-writes by deleting the target directory before writing. If old files persist, manually delete `.agents/converter/<target>/<skill>/` |
| `--all` skips a skill directory | The directory has no `SKILL.md` file | Ensure each skill directory contains a valid `SKILL.md`. Run Heal Skill to detect empty directories |
| Codex `prompt.md` description is truncated | The skill description exceeds 1024 characters | This is by design. The converter truncates at a word boundary to fit Codex limits. Shorten the description in SKILL.md frontmatter if the truncation point is awkward |
| Conversion fails with passthrough parity check | A resource entry from source skill wasn't copied to output | Ensure source entries are readable and copyable (including nested files). Re-run conversion; failure is intentional to prevent drift between `skills/` and converted output |

## Output Specification

- **Path:** `.agents/converter/<target>/<skill-name>/` by default, or the exact caller-supplied output directory.
- **Filename:** Codex emits `SKILL.md`, `prompt.md`, and copied resources; Cursor emits `<skill-name>.mdc` and optional `mcp.json`; `test` emits the raw bundle representation.
- **Format:** target-valid UTF-8 text with required frontmatter, rewritten runtime references, and byte-present passthrough resources; Cursor output remains within 100KB.
- **Exit code:** run `bash skills/converter/scripts/convert.sh <skill-dir> <target> <output-dir>` and require zero; treat parse, budget, write, or passthrough-parity failure as nonzero and incomplete.
- **Downstream handoff:** report the source skill, target, output directory, layout, omitted Cursor references if any, and validation result to the installer or projection gate.

## Quality Checklist

- The source tree is unchanged and the output tree contains no files left over from an earlier conversion.
- Every required target file parses with its target frontmatter/schema and every eligible source resource is present.
- Runtime-specific rewrites preserve the source meaning without reintroducing deprecated command forms or foreign-runtime paths.

## References

- `references/skill-bundle-schema.md` -- SkillBundle interchange format specification

## Reference Documents

- [references/skill-bundle-schema.md](references/skill-bundle-schema.md)
