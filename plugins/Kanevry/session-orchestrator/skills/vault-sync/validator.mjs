#!/usr/bin/env node
/**
 * validator.mjs — Meta-Vault frontmatter + wiki-link validator (Phase 1).
 *
 * Reads every `.md` file under VAULT_DIR, parses YAML frontmatter, validates
 * against the canonical vaultFrontmatterSchema, and checks wiki-link targets
 * resolve inside the vault. Emits a machine-readable JSON report to stdout and
 * exits 0 on clean vault (warnings allowed), 1 on validation errors, 0 when
 * there is no vault to validate.
 *
 * ── Schema drift ────────────────────────────────────────────────────────────
 * The Zod schema below is auto-vendored from the canonical source:
 *   projects-baseline/packages/zod-schemas/src/vault-frontmatter.ts
 * This skill is intentionally self-contained (no workspace dependency on the
 * shared monorepo package), so the schema is vendored here via the managed
 * sync script: scripts/sync-vault-schema.mjs
 *
 * To update after a canonical change, run:
 *   node scripts/sync-vault-schema.mjs --write
 * then commit the resulting validator.mjs diff.
 *
 * The schema block below is fenced by a pair of sentinel comments managed by
 * sync-vault-schema.mjs. DO NOT edit between them by hand — any manual edit
 * will be overwritten on the next --write run and will cause --check to report
 * drift.
 *
 * Drift is gated by tests/schema-drift.test.mjs (5 scenarios: idempotency,
 * --check clean, --check drift, missing canonical, sentinel presence) and
 * by the GitLab CI pipeline which runs --check mode against a freshly-cloned
 * canonical to catch any out-of-band edits.
 *
 * 2026-04-13: tagPathRegex added for Obsidian nested-tag support (e.g. meta/schema).
 *
 * 2026-05-23 (#503, I5): `peer-card` appended to vaultNoteTypeSchema via the
 *   vendored-edit + sync-script-baseline-update path. Upstream canonical
 *   (projects-baseline/packages/zod-schemas/src/vault-frontmatter.ts) is
 *   behind until #503 lands there; until then, `sync-vault-schema.mjs --check`
 *   will report drift in CI. Tracked as upstream-sync-debt in the #503 PRD.
 *   When upstream catches up, re-run `node scripts/sync-vault-schema.mjs --write`
 *   to confirm idempotency.
 *
 * 2026-07-02 (#725, D2): `'source-repo': z.string().optional()` appended to
 *   vaultFrontmatterSchema (same vendored-ahead pattern as #503). vault-mirror
 *   now emits `source-repo` in generated learning notes for cross-repo
 *   attribution (scripts/lib/vault-mirror/render-learnings.mjs). The field is
 *   OPTIONAL — pre-existing notes without it stay valid, and `.passthrough()`
 *   already accepted the key; the explicit declaration adds string-type
 *   enforcement. Upstream canonical is behind until #725 lands there, so
 *   `sync-vault-schema.mjs --check` reports drift in CI (upstream-sync-debt).
 *   Re-run `--write` once upstream catches up to confirm idempotency.
 *
 * 2026-07-03 (#738, I2): `board` appended to vaultNoteTypeSchema so the
 *   generated `01-projects/_active-sessions.md` board validates as a
 *   first-class vault note. Upstream canonical sync remains out of scope for
 *   this worker because the baseline repo is intentionally dirty.
 * ────────────────────────────────────────────────────────────────────────────
 */

import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join, relative, resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';
import YAML from 'yaml';
import { resolveInstructionFile } from '../../scripts/lib/common.mjs';
import {
  computeSchemaHash,
  writeBaseline,
  readBaseline,
  diffBaseline,
} from '../../scripts/lib/vault-sync-baseline.mjs';

// ── Inline vendored schema (mirrors projects-baseline vault-frontmatter.ts) ──
// ── BEGIN GENERATED SCHEMA (sync-vault-schema.mjs) — do not edit between sentinels ──
const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const tagPathRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*(?:\/[a-z0-9]+(?:-[a-z0-9]+)*)*$/;

const isoDateRegex =
  /^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?)?$/;

const vaultNoteTypeSchema = z.enum([
  'note',
  'daily',
  'project',
  'person',
  'reference',
  'idea',
  'learning',
  'session',
  'peer-card',
  'board',
]);

const vaultNoteStatusSchema = z.enum([
  'draft',
  'active',
  'verified',
  'archived',
  'production',
  'mvp',
  'idea',
]);

const vaultFrontmatterSchema = z
  .object({
    id: z
      .string()
      .regex(slugRegex, 'Ungueltige id (kebab-case slug format required)')
      .min(2)
      .max(128),
    type: vaultNoteTypeSchema,
    created: z.string().regex(isoDateRegex, 'Ungueltiges Datum (ISO 8601 required)'),
    updated: z.string().regex(isoDateRegex, 'Ungueltiges Datum (ISO 8601 required)'),
    title: z.string().min(1).max(200).optional(),
    tags: z
      .array(
        z
          .string()
          .regex(tagPathRegex, 'Ungueltiger tag (kebab-case segments joined by / — e.g. meta/schema)')
          .min(1)
          .max(64),
      )
      .optional(),
    status: vaultNoteStatusSchema.optional(),
    expires: z
      .string()
      .regex(isoDateRegex, 'Ungueltiges Datum (ISO 8601 required)')
      .optional(),
    source: z.string().optional(),
    sources: z.array(z.string()).optional(),
    aliases: z.array(z.string().min(1).max(200)).optional(),
    'source-repo': z.string().optional(),
  })
  .passthrough();
// ── END GENERATED SCHEMA ──

// ── Schema hash (module-scope cached) ───────────────────────────────────────
// Extract the vendored schema text between the BEGIN/END sentinels in this
// file's own source and compute a stable 8-char SHA-256 prefix. Used by
// --mode=baseline (to stamp snapshots) and --mode=diff (to detect schema drift
// between a stored baseline and the current validator revision).
const _schemaHash = (() => {
  try {
    const selfPath = fileURLToPath(import.meta.url);
    const src = readFileSync(selfPath, 'utf8');
    const begin = '── BEGIN GENERATED SCHEMA';
    const end = '── END GENERATED SCHEMA ──';
    const beginIdx = src.indexOf(begin);
    const endIdx = src.indexOf(end);
    if (beginIdx === -1 || endIdx === -1 || endIdx <= beginIdx) return 'unknown';
    const schemaBlock = src.slice(beginIdx, endIdx + end.length);
    return computeSchemaHash(schemaBlock);
  } catch {
    return 'unknown';
  }
})();

// ── CLI args ────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const checkExpires = args.includes('--check-expires');

// Parse --mode <hard|warn|off|baseline|diff|full> (default: hard)
//   hard      — legacy alias; identical to full enforcement
//   full      — enforce: exit 1 on errors
//   warn      — report but exit 0
//   off       — skip entirely
//   baseline  — write snapshot then exit 0
//   diff      — compare against snapshot, emit JSON diff
// Parse --exclude <glob> (repeatable)
let mode = 'hard';
const excludePatterns = [];

// ── Unconditional config-loaded excludes (issue #329) ──────────────────────
// Read `vault-sync.exclude` from <VAULT_DIR>/CLAUDE.md (or AGENTS.md) BEFORE
// parsing argv so that bare invocations (no caller, no --exclude flags) still
// honour the project's configured exclusion list. CLI --exclude flags below
// are additive — they extend (do not replace) the config-loaded list.
//
// Resolution order for the directory:
//   1. process.env.VAULT_DIR (absolute or relative to cwd)
//   2. process.cwd() fallback
//
// Wrapped in try/catch: missing CLAUDE.md, missing module, or parse error all
// degrade silently to "no config excludes" — the validator must continue to
// work on repos that have no project-instruction file.
try {
  const configDir = process.env.VAULT_DIR ? resolve(process.env.VAULT_DIR) : process.cwd();
  const instr = resolveInstructionFile(configDir);
  if (instr && existsSync(instr.path)) {
    const content = readFileSync(instr.path, 'utf8');
    const { _parseVaultSync } = await import('../../scripts/lib/config/vault-sync.mjs');
    const parsed = _parseVaultSync(content);
    if (Array.isArray(parsed.exclude)) {
      for (const pat of parsed.exclude) {
        if (typeof pat === 'string' && pat.length > 0) excludePatterns.push(pat);
      }
    }
  }
} catch {
  // Silent fallback: validator must work without CLAUDE.md / config parser.
}

for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--mode') {
    const v = args[i + 1];
    if (v === 'hard' || v === 'warn' || v === 'off' || v === 'baseline' || v === 'diff' || v === 'full') {
      mode = v;
    } else {
      process.stderr.write(
        `validator.mjs: invalid --mode value "${v}" (expected hard|warn|off|baseline|diff|full)\n`,
      );
      process.exit(2);
    }
    i++;
  } else if (a.startsWith('--mode=')) {
    const v = a.slice('--mode='.length);
    if (v === 'hard' || v === 'warn' || v === 'off' || v === 'baseline' || v === 'diff' || v === 'full') {
      mode = v;
    } else {
      process.stderr.write(
        `validator.mjs: invalid --mode value "${v}" (expected hard|warn|off|baseline|diff|full)\n`,
      );
      process.exit(2);
    }
  } else if (a === '--exclude') {
    if (args[i + 1]) {
      excludePatterns.push(args[i + 1]);
      i++;
    }
  } else if (a.startsWith('--exclude=')) {
    excludePatterns.push(a.slice('--exclude='.length));
  }
}

// ── Tiny fnmatch-style glob matcher ─────────────────────────────────────────
// Supports:
//   **    — any number of path segments (zero or more)
//   *     — any characters except `/`
//   ?     — any single character except `/`
//   literal path separators and characters otherwise
// Operates on POSIX-style forward-slash relative paths.
function globToRegExp(glob) {
  // Normalise input
  const g = glob.replace(/\\/g, '/');
  let re = '^';
  for (let i = 0; i < g.length; i++) {
    const c = g[i];
    if (c === '*') {
      if (g[i + 1] === '*') {
        // `**` — match across path segments
        // Also swallow a following `/` so that `**/foo` matches `foo` at root.
        const nextSlash = g[i + 2] === '/';
        re += '(?:.*?)';
        if (nextSlash) i += 2;
        else i += 1;
      } else {
        re += '[^/]*';
      }
    } else if (c === '?') {
      re += '[^/]';
    } else if ('.+^$(){}|[]\\'.includes(c)) {
      re += '\\' + c;
    } else {
      re += c;
    }
  }
  re += '$';
  return new RegExp(re);
}

const excludeRegexes = excludePatterns.map((p) => globToRegExp(p));

function isExcluded(relPath) {
  const p = relPath.replace(/\\/g, '/');
  for (const re of excludeRegexes) {
    if (re.test(p)) return true;
  }
  return false;
}

// ── Vault marker detection ──────────────────────────────────────────────────
// Returns true if dir contains at least one recognized vault marker:
//   1. _meta/ directory
//   2. CLAUDE.md or AGENTS.md (alias — see skills/_shared/instruction-file-resolution.md)
//      containing both "## Session Config" and "vault-sync:". The instruction
//      file is resolved via resolveInstructionFile() so CLAUDE.md wins ties and
//      AGENTS.md is accepted on Codex CLI repos.
//   3. .obsidian/ directory
function isVaultDir(dir) {
  if (existsSync(join(dir, '_meta')) && statSync(join(dir, '_meta')).isDirectory()) return true;
  if (existsSync(join(dir, '.obsidian')) && statSync(join(dir, '.obsidian')).isDirectory()) return true;
  const instr = resolveInstructionFile(dir);
  if (instr) {
    try {
      const content = readFileSync(instr.path, 'utf8');
      if (content.includes('## Session Config') && content.includes('vault-sync:')) return true;
    } catch {
      // unreadable instruction file — not a vault marker
    }
  }
  return false;
}

// ── Resolve vault dir ───────────────────────────────────────────────────────
let vaultDir;
if (process.env.VAULT_DIR) {
  vaultDir = resolve(process.env.VAULT_DIR);
  // Only warn when the directory exists but lacks vault markers.
  // Non-existent dirs are handled further down by the existsSync guard (status: skipped).
  if (existsSync(vaultDir) && statSync(vaultDir).isDirectory() && !isVaultDir(vaultDir)) {
    process.stderr.write(
      'vault-sync: warning: VAULT_DIR set but directory lacks vault markers (_meta/, CLAUDE.md or AGENTS.md with vault-sync, or .obsidian/)\n',
    );
  }
} else {
  const cwd = process.cwd();
  if (isVaultDir(cwd)) {
    vaultDir = resolve(cwd);
  } else {
    process.stderr.write(
      [
        'vault-sync: error: VAULT_DIR is not set and the current working directory does not look like a Meta-Vault.',
        '',
        'Expected one of the following in cwd:',
        '  - _meta/ directory',
        "  - CLAUDE.md (or AGENTS.md on Codex CLI) with a '## Session Config' and 'vault-sync:' block",
        '  - .obsidian/ directory',
        '',
        'Fix: set VAULT_DIR to the vault root, or cd into the vault before running.',
        '',
      ].join('\n'),
    );
    process.exit(2);
  }
}

const EXCLUDED_DIRS = new Set([
  'node_modules',
  '.git',
  '.obsidian',
  '90-archive',
]);

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

// Mode off → no-op (useful for onboarding / emergency bypass).
if (mode === 'off') {
  emit({
    status: 'skipped-mode-off',
    mode,
    vault_dir: vaultDir,
    files_checked: 0,
    excluded_count: 0,
    files_skipped_no_frontmatter: 0,
    errors: [],
    warnings: [],
  });
  process.exit(0);
}

// No vault to check → skipped.
if (!existsSync(vaultDir) || !statSync(vaultDir).isDirectory()) {
  emit({ status: 'skipped', reason: 'no vault', mode, vault_dir: vaultDir });
  process.exit(0);
}

// ── Crawl .md files ─────────────────────────────────────────────────────────
function walk(dir, out) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    if (e.name.startsWith('.') && e.name !== '.') {
      // always skip dot-dirs/files except allow top-level
      if (e.isDirectory() && EXCLUDED_DIRS.has(e.name)) continue;
      if (e.isDirectory()) continue;
      // skip hidden files
      continue;
    }
    if (e.isDirectory()) {
      if (EXCLUDED_DIRS.has(e.name)) continue;
      walk(join(dir, e.name), out);
    } else if (e.isFile() && e.name.endsWith('.md')) {
      out.push(join(dir, e.name));
    }
  }
}

const mdFiles = [];
walk(vaultDir, mdFiles);

if (mdFiles.length === 0) {
  emit({ status: 'skipped', reason: 'no vault', mode, vault_dir: vaultDir });
  process.exit(0);
}

// ── Parse frontmatter ───────────────────────────────────────────────────────
const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/;

function parseFrontmatter(raw) {
  const m = raw.match(FRONTMATTER_RE);
  if (!m) return { hasFrontmatter: false };
  const yamlBlock = m[1];
  try {
    const data = YAML.parse(yamlBlock);
    return { hasFrontmatter: true, data: data ?? {}, raw: yamlBlock };
  } catch (err) {
    return { hasFrontmatter: true, parseError: err.message || String(err) };
  }
}

// ── Build link index (filename -> path) ─────────────────────────────────────
const fileIndex = new Map(); // basename-without-ext -> [absolute paths]
for (const f of mdFiles) {
  const key = basename(f, '.md');
  if (!fileIndex.has(key)) fileIndex.set(key, []);
  fileIndex.get(key).push(f);
}

// ── Wiki-link regex — captures link body for target parsing ─────────────────
const WIKILINK_RE = /\[\[([^\]]+)\]\]/g;

function findAliasSeparatorIndex(linkBody) {
  for (let i = 0; i < linkBody.length; i++) {
    if (linkBody[i] === '\\' && linkBody[i + 1] === '|') return i;
    if (linkBody[i] === '|') return i;
  }
  return -1;
}

function extractWikiLinkTarget(linkBody) {
  const aliasIndex = findAliasSeparatorIndex(linkBody);
  const targetWithAnchor = aliasIndex === -1 ? linkBody : linkBody.slice(0, aliasIndex);
  return targetWithAnchor.split('#', 1)[0].trim();
}

function extractWikiLinks(content) {
  const targets = new Set();
  let m;
  while ((m = WIKILINK_RE.exec(content)) !== null) {
    const target = extractWikiLinkTarget(m[1]);
    if (target.length > 0) targets.add(target);
  }
  return [...targets];
}

function resolveWikiLink(target, sourceFile) {
  // Target may be a bare name ("my-note") or a path ("01-projects/foo/_overview").
  // Try exact path first (relative to vault), then basename lookup.
  const candidate1 = resolve(vaultDir, target.endsWith('.md') ? target : target + '.md');
  if (existsSync(candidate1)) return true;

  // Try relative to source file's directory
  const candidate2 = resolve(
    dirname(sourceFile),
    target.endsWith('.md') ? target : target + '.md',
  );
  if (existsSync(candidate2)) return true;

  // Try basename lookup anywhere in index
  const key = basename(target, '.md');
  if (fileIndex.has(key)) return true;

  return false;
}

// ── Validate each file ──────────────────────────────────────────────────────
const errors = [];
const warnings = [];
let filesChecked = 0;
let filesSkippedNoFrontmatter = 0;
let excludedCount = 0;

const todayIso = new Date().toISOString().slice(0, 10);

for (const file of mdFiles) {
  const rel = relative(vaultDir, file);
  if (isExcluded(rel)) {
    excludedCount++;
    continue;
  }
  let raw;
  try {
    raw = readFileSync(file, 'utf8');
  } catch (err) {
    errors.push({
      file: rel,
      path: '',
      message: `Cannot read file: ${err.message || err}`,
    });
    continue;
  }

  const fm = parseFrontmatter(raw);

  if (!fm.hasFrontmatter) {
    filesSkippedNoFrontmatter++;
    continue;
  }

  filesChecked++;

  if (fm.parseError) {
    errors.push({
      file: rel,
      path: 'frontmatter',
      message: `YAML parse error: ${fm.parseError}`,
    });
    continue;
  }

  const parsed = vaultFrontmatterSchema.safeParse(fm.data);
  if (!parsed.success) {
    for (const issue of parsed.error.issues) {
      errors.push({
        file: rel,
        path: issue.path.join('.'),
        message: issue.message,
      });
    }
    // Even if frontmatter is invalid, still check wiki-links to surface all problems.
  }

  // Wiki-link check
  const body = raw.slice(raw.match(FRONTMATTER_RE)?.[0].length || 0);
  const links = extractWikiLinks(body);
  for (const target of links) {
    if (!resolveWikiLink(target, file)) {
      warnings.push({
        file: rel,
        type: 'dangling-wiki-link',
        message: `Wiki-link target not found in vault: [[${target}]]`,
      });
    }
  }

  // Expires check (opt-in)
  if (checkExpires && parsed.success && parsed.data.expires) {
    if (parsed.data.expires < todayIso) {
      warnings.push({
        file: rel,
        type: 'expired',
        message: `Note expired on ${parsed.data.expires} (today is ${todayIso})`,
      });
    }
  }
}

const hasErrors = errors.length > 0;

// ── mode=baseline ─────────────────────────────────────────────────────────
// Serialize current errors + warnings as a snapshot, then exit 0.
if (mode === 'baseline') {
  const baselinePath = join(vaultDir, '.orchestrator', 'metrics', 'vault-sync-baseline.json');
  writeBaseline(baselinePath, {
    errors,
    warnings,
    schemaHash: _schemaHash,
    isoTimestamp: new Date().toISOString(),
    vaultDir,
  });
  process.stderr.write(
    `WRITE: baseline -> ${baselinePath} (${errors.length} errors, ${warnings.length} warnings)\n`,
  );
  process.exit(0);
}

// ── mode=diff ─────────────────────────────────────────────────────────────
// Read a prior baseline, compute set-differences, emit JSON diff to stdout.
if (mode === 'diff') {
  const baselinePath = join(vaultDir, '.orchestrator', 'metrics', 'vault-sync-baseline.json');
  const baseline = readBaseline(baselinePath);

  if (!baseline) {
    // No baseline file at all — fall back to full enforcement.
    process.stderr.write(
      `WARN: no baseline found at ${baselinePath} — falling back to full enforcement. Run --mode=baseline to create a snapshot.\n`,
    );
    const statusFull = hasErrors ? 'invalid' : 'ok';
    emit({
      status: statusFull,
      mode: 'diff-fallback-full',
      vault_dir: vaultDir,
      files_checked: filesChecked,
      excluded_count: excludedCount,
      files_skipped_no_frontmatter: filesSkippedNoFrontmatter,
      errors,
      warnings,
    });
    process.exit(hasErrors ? 1 : 0);
  }

  if (baseline.schemaHash !== _schemaHash) {
    process.stderr.write(
      `WARN: baseline outdated (hash=${baseline.schemaHash}, current=${_schemaHash}) — please re-snapshot via --mode=baseline\n`,
    );
    // Schema drift — fall back to full enforcement.
    const statusFull = hasErrors ? 'invalid' : 'ok';
    emit({
      status: statusFull,
      mode: 'diff-fallback-full',
      vault_dir: vaultDir,
      files_checked: filesChecked,
      excluded_count: excludedCount,
      files_skipped_no_frontmatter: filesSkippedNoFrontmatter,
      errors,
      warnings,
    });
    process.exit(hasErrors ? 1 : 0);
  }

  const errorDiff = diffBaseline({ baselineErrors: baseline.errors, currentErrors: errors });
  const warningDiff = diffBaseline({ baselineErrors: baseline.warnings, currentErrors: warnings });

  emit({
    new_errors: errorDiff.newErrors,
    resolved_errors: errorDiff.resolvedErrors,
    new_warnings: warningDiff.newErrors,
    resolved_warnings: warningDiff.resolvedErrors,
    baseline_count: errorDiff.baselineCount,
    current_count: errorDiff.currentCount,
    schema_hash: _schemaHash,
    vault_dir: vaultDir,
    files_checked: filesChecked,
    excluded_count: excludedCount,
    files_skipped_no_frontmatter: filesSkippedNoFrontmatter,
  });

  process.stderr.write(
    `baseline=${errorDiff.baselineCount} current=${errorDiff.currentCount} new=${errorDiff.newErrors.length} resolved=${errorDiff.resolvedErrors.length}\n`,
  );

  process.exit(errorDiff.newErrors.length === 0 ? 0 : 1);
}

// ── mode=full | hard | warn ───────────────────────────────────────────────
// 'full' and 'hard' are identical (hard is the legacy alias).
// In warn mode, errors are reported but the status is "ok" for exit-code purposes.
// The errors array is still populated so the caller can surface them as warnings.
const status = hasErrors ? (mode === 'warn' ? 'ok' : 'invalid') : 'ok';
emit({
  status,
  mode,
  vault_dir: vaultDir,
  files_checked: filesChecked,
  excluded_count: excludedCount,
  files_skipped_no_frontmatter: filesSkippedNoFrontmatter,
  errors,
  warnings,
});

process.exit(hasErrors && (mode === 'hard' || mode === 'full') ? 1 : 0);
