#!/usr/bin/env node
/**
 * checker.mjs — CLAUDE.md narrative drift-check (claude-md-drift-check).
 *
 * Ten checks: path-resolver, project-count-sync, issue-reference-freshness,
 * session-file-existence, surface-count (command/skill/agent/hook-event/
 * hook-matcher/test families), session-config-parity, vault-dir-parity,
 * generated-rule-staleness (WARN-mode only), rule-scoping (paths-presence,
 * cited-but-missing rule citations, zero-match-globs, and foreign-glob
 * PascalCase tokens in .claude/rules/*.md frontmatter), and docs-parity
 * (count-claims in docs/components.md vs actual on-disk counts, Session-Config
 * key parity between docs/session-config-template.md and
 * docs/session-config-reference.md, and stale `.claude/metrics/` path
 * references in the live docs tree).
 * Scans CLAUDE.md + _meta/**\/*.md by default.
 * Emits JSON on stdout. Exit 0 (ok/warn/skip), 1 (hard + errors), 2 (infra).
 *
 * The surface-count family (issue #663) generalizes the original command-count
 * drift check into a parity guard over six artifact surfaces. Each surface
 * derives an ACTUAL on-disk count (glob / hooks.json wiring) and compares it
 * against a CLAIMED count extracted by regex from any scanned doc (README.md,
 * .orchestrator/steering/structure.md, CLAUDE.md). A surface that the doc never
 * claims numerically is skipped gracefully — no claim is ever invented.
 *
 * Reuses `_parseVaultIntegration` from scripts/lib/config/ for Check 7;
 * reuses `parseGlobsFrontmatter` from scripts/lib/rule-loader.mjs for Check 9's
 * glob extraction (mirrors the same picomatch-with-inline-fallback resolution
 * rule-loader.mjs uses); otherwise pure Node stdlib.
 */

import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { resolveInstructionFile } from '../../scripts/lib/common.mjs';
import { _parseVaultIntegration } from '../../scripts/lib/config/vault-integration.mjs';
import { parseGlobsFrontmatter } from '../../scripts/lib/rule-loader.mjs';

const FORWARD_HEADING_RE =
  /(?:^|\b)(what'?s?\s+next|backlog|open\s+issues?|offene\s+(?:issues?|themen)|todo|next\s+steps?|roadmap)(?:$|\b)/i;
const BACKWARD_HEADING_RE =
  /(?:^|\b)(recently\s+closed|done|closed|archive|history|changelog|decisions?|status|references?)(?:$|\b)/i;

function parseArgs(argv) {
  const out = {
    mode: 'warn',
    includePaths: [],
    skipPathResolver: false,
    skipProjectCount: false,
    skipIssueRefs: false,
    skipSessionFiles: false,
    skipCommandCount: false,
    skipSurfaceCount: false,
    skipSessionConfigParity: false,
    skipVaultDirParity: false,
    skipGeneratedRuleStaleness: false,
    skipRuleScoping: false,
    skipDocsParity: false,
    repo: null,
    commandsDir: null,
    configTemplate: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--mode') out.mode = argv[++i];
    else if (a === '--include-path') out.includePaths.push(argv[++i]);
    else if (a === '--repo') out.repo = argv[++i];
    else if (a === '--commands-dir') out.commandsDir = argv[++i];
    else if (a === '--config-template') out.configTemplate = argv[++i];
    else if (a === '--skip-path-resolver') out.skipPathResolver = true;
    else if (a === '--skip-project-count') out.skipProjectCount = true;
    else if (a === '--skip-issue-refs') out.skipIssueRefs = true;
    else if (a === '--skip-session-files') out.skipSessionFiles = true;
    else if (a === '--skip-command-count') out.skipCommandCount = true;
    else if (a === '--skip-surface-count') out.skipSurfaceCount = true;
    else if (a === '--skip-session-config-parity') out.skipSessionConfigParity = true;
    else if (a === '--skip-vault-dir-parity') out.skipVaultDirParity = true;
    else if (a === '--skip-generated-rule-staleness') out.skipGeneratedRuleStaleness = true;
    else if (a === '--skip-rule-scoping') out.skipRuleScoping = true;
    else if (a === '--skip-docs-parity') out.skipDocsParity = true;
    else if (a === '--help' || a === '-h') {
      process.stdout.write('Usage: checker.mjs [--mode strict|warn|off] [--include-path GLOB]... [--repo OWNER/NAME] [--commands-dir PATH] [--config-template PATH] [--skip-surface-count] [--skip-command-count] [--skip-generated-rule-staleness] [--skip-rule-scoping] [--skip-docs-parity] [--skip-*]\n');
      process.exit(0);
    } else {
      process.stderr.write(`{"status":"infra-error","reason":"unknown arg: ${a}"}\n`);
      process.exit(2);
    }
  }
  // Defaults for includePaths are seeded post-vaultDir resolution so the
  // instruction file (CLAUDE.md or AGENTS.md alias) can be alias-resolved.
  return out;
}

function resolveScopeFiles(vaultDir, patterns) {
  const files = new Set();
  for (const pattern of patterns) {
    if (pattern.includes('**/')) {
      const [prefix, suffix] = pattern.split('/**/');
      const extMatch = /^\*\.(\w+)$/.exec(suffix || '');
      const ext = extMatch ? `.${extMatch[1]}` : null;
      const dir = join(vaultDir, prefix);
      if (existsSync(dir) && statSync(dir).isDirectory()) {
        walkDir(dir, (f) => {
          if (!ext || f.endsWith(ext)) files.add(f);
        });
      }
    } else {
      const abs = join(vaultDir, pattern);
      if (existsSync(abs) && statSync(abs).isFile()) files.add(abs);
    }
  }
  return Array.from(files).sort();
}

function walkDir(dir, visit) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walkDir(full, visit);
    else if (entry.isFile()) visit(full);
  }
}

/**
 * Extract the YAML block under a `## Session Config` heading from a Markdown
 * document. Tries fenced YAML first (```yaml ... ```) *within the matched
 * heading's own body slice*, then falls back to the raw body up to the next
 * `^## ` heading or EOF.
 *
 * `docs/session-config-template.md` carries TWO literal `## Session Config`
 * lines — both live INSIDE fenced ```yaml example blocks: the "Full minimal
 * baseline" (7 mandatory keys) and the "Full opt-in baseline" (the complete
 * key catalog, a strict superset of the minimal block). By default this
 * function matches the FIRST occurrence (correct for a local CLAUDE.md /
 * AGENTS.md instruction file, which has exactly one real heading). Pass
 * `{ occurrence: 'last' }` to match the LAST occurrence instead — the template
 * call site uses this to reach the opt-in baseline's full key set rather than
 * silently stopping at the 7-key minimal block (issue #785).
 *
 * Returns { body: string, headingLine: number } or null when no heading found.
 *
 * @param {string} content
 * @param {{ occurrence?: 'first'|'last' }} [options]
 */
function extractSessionConfigBlock(content, { occurrence = 'first' } = {}) {
  const lines = content.split('\n');
  const headingIdxs = [];
  for (let i = 0; i < lines.length; i++) {
    if (/^##\s+Session Config\b/.test(lines[i])) headingIdxs.push(i);
  }
  if (headingIdxs.length === 0) return null;

  const targetIdx = occurrence === 'last' ? headingIdxs[headingIdxs.length - 1] : headingIdxs[0];
  const headingLine = targetIdx + 1; // 1-based line number for error reporting

  // Raw body: from the line after the heading up to the next `## ` heading or EOF.
  let endIdx = lines.length;
  for (let i = targetIdx + 1; i < lines.length; i++) {
    if (/^##\s+/.test(lines[i])) { endIdx = i; break; }
  }
  const rawBody = lines.slice(targetIdx + 1, endIdx).join('\n');

  // Prefer a fenced YAML block found anywhere within the raw body slice
  // (tolerates a blank line between the heading and the fence); fall back to
  // the raw body itself when no fence is present.
  const fenced = rawBody.match(/```ya?ml\r?\n([\s\S]*?)\r?\n```/);
  const body = fenced ? fenced[1] : rawBody;

  return { body, headingLine };
}

/**
 * Extract top-level YAML keys from a YAML body. Only column-0 keys are
 * collected (indented keys are children and ignored).
 */
function extractTopLevelKeys(body) {
  const keys = [];
  const re = /^([A-Za-z][\w-]*):/gm;
  let m;
  while ((m = re.exec(body)) !== null) {
    keys.push(m[1]);
  }
  return keys;
}

/**
 * Extract Session-Config-key-shaped mentions from a "reference" style doc
 * (docs/session-config-reference.md for Check 10b). Unlike the template,
 * which carries one big fenced Session Config block, the reference documents
 * most fields as ONE MARKDOWN TABLE ROW PER KEY (`| \`key-name\` | type |
 * default | description |`) rather than in a single YAML block — a plain
 * "union all yaml fences" extraction (as in `extractSessionConfigBlock`)
 * massively under-counts what the reference actually documents (verified:
 * 53 false-positive "missing" keys against the live doc when restricted to
 * fences/headings alone, vs. the true gap of 6 keys once table rows are
 * counted). Three surfaces contribute to the returned key set:
 *   - top-level keys inside any ```yaml fenced block (any indent depth);
 *   - `##`/`###`/`####` heading key-tokens (optionally backtick-wrapped),
 *     e.g. "## Templates-First Hook" → no match (not kebab-lowercase-shaped),
 *     "### resource-thresholds" → `resource-thresholds`;
 *   - the FIRST CELL of a markdown table row when it is a backtick-wrapped
 *     kebab-case token, e.g. `| \`plan-prd-location\` | string | ... |`.
 * Fence state is tracked for ALL code fences (not just yaml-tagged ones) so
 * headings/table-rows accidentally written inside an unrelated code example
 * are not mistaken for real documentation structure.
 *
 * @param {string} content
 * @returns {Set<string>}
 */
function extractDocKeyMentions(content) {
  const keys = new Set();
  const lines = content.split('\n');
  let inFence = false;
  let fenceLang = null;
  let fenceBuf = [];
  for (const line of lines) {
    if (!inFence) {
      const fenceOpen = /^```\s*(\w*)\s*$/.exec(line);
      if (fenceOpen) { inFence = true; fenceLang = fenceOpen[1]; fenceBuf = []; continue; }
    } else {
      if (/^```\s*$/.test(line)) {
        inFence = false;
        if (/^ya?ml$/i.test(fenceLang || '')) {
          const re = /^\s*([a-z][\w-]*):/gm;
          let m;
          const body = fenceBuf.join('\n');
          while ((m = re.exec(body)) !== null) keys.add(m[1]);
        }
        continue;
      }
      fenceBuf.push(line);
      continue;
    }

    const heading = /^#{2,4}\s+`?([a-z][\w-]*)`?/.exec(line);
    if (heading) keys.add(heading[1]);

    const tableRow = /^\|\s*`([a-z][\w-]*)`\s*\|/.exec(line);
    if (tableRow) keys.add(tableRow[1]);
  }
  return keys;
}

/**
 * Read a file's `vault-integration` settings for the vault-dir-parity check.
 *
 * Returns `{ present, vaultDir }`:
 *   - `present` is true when the file contains a `vault-integration:` block or
 *     inline-object literal (block-form header `vault-integration:` on its own
 *     line, or `vault-integration: { ... }`), matching the source shapes
 *     `_parseVaultIntegration` recognises.
 *   - `vaultDir` is the parsed `vault-integration.vault-dir` value (null when
 *     unset/absent), produced by reusing `_parseVaultIntegration` rather than
 *     hand-rolling YAML.
 *
 * @param {string} filePath — absolute path to CLAUDE.md / AGENTS.md
 * @returns {{ present: boolean, vaultDir: string|null }}
 */
function readVaultIntegration(filePath) {
  const content = readFileSync(filePath, 'utf8');
  // Detect block-form header (`vault-integration:` alone on a line) or inline
  // object literal (`vault-integration: { ... }`), with or without a list dash.
  const present =
    /^(?:-\s+)?vault-integration:\s*$/m.test(content) ||
    /^(?:-\s+)?vault-integration:\s*\{[^}]*\}\s*(?:#.*)?$/m.test(content);
  const parsed = _parseVaultIntegration(content);
  return { present, vaultDir: parsed['vault-dir'] };
}

function classifySection(heading) {
  if (!heading) return null;
  if (BACKWARD_HEADING_RE.test(heading)) return 'backward';
  if (FORWARD_HEADING_RE.test(heading)) return 'forward';
  return null;
}

// ───────────────────────────────────────────────────────────────────────────
// Surface-count family (issue #663) — generalizes the original command-count
// drift check. Each surface has:
//   - id:    the check id surfaced in errors[].check and checks_run.
//   - actual(vaultDir): pure function returning the ACTUAL on-disk count, or
//            null when the source artifact is absent (→ surface skipped).
//   - claimRe: a /g/i regex whose capture group 1 is the CLAIMED integer. Only
//            an explicit numeric claim triggers a comparison; surfaces with no
//            matching phrase in any doc are skipped gracefully (requirement #3).
//   - noun:  human label used in the drift message.
// These are EXACT-count drift checks by design — the whole point is catching
// drift, so NO floor/ceiling (see .claude/rules/testing.md "Dynamic Artifact
// Counts" carve-out — this is the explicit exception).
// ───────────────────────────────────────────────────────────────────────────

/** Count `skills/<name>/SKILL.md` directories (excludes `_shared/` which has no SKILL.md). */
function countSkills(vaultDir) {
  const dir = join(vaultDir, 'skills');
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return null;
  let n = 0;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
    const skillFile = join(dir, entry.name, 'SKILL.md');
    if (existsSync(skillFile) && statSync(skillFile).isFile()) n++;
  }
  return n;
}

/** Count `agents/*.md` definitions, excluding the AGENTS.md authoring spec. */
function countAgents(vaultDir) {
  const dir = join(vaultDir, 'agents');
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return null;
  return readdirSync(dir)
    .filter((f) => f.endsWith('.md') && f !== 'AGENTS.md' && !f.startsWith('.'))
    .length;
}

/**
 * Parse `hooks/hooks.json` and return `{ events, matchers }`:
 *   - events:   distinct top-level event names (keys of `.hooks`).
 *   - matchers: total matcher entries across all events (the authoritative
 *               wiring count, not a raw file count).
 * Returns null when hooks.json is absent or unparseable.
 */
function readHookCounts(vaultDir) {
  const file = join(vaultDir, 'hooks', 'hooks.json');
  if (!existsSync(file) || !statSync(file).isFile()) return null;
  let json;
  try {
    json = JSON.parse(readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
  const hooks = json && json.hooks;
  if (!hooks || typeof hooks !== 'object') return null;
  const events = Object.keys(hooks);
  let matchers = 0;
  for (const ev of events) {
    if (Array.isArray(hooks[ev])) matchers += hooks[ev].length;
  }
  return { events: events.length, matchers };
}

/** Count test files (`*.test.mjs`) under `tests/`. */
function countTestFiles(vaultDir) {
  const dir = join(vaultDir, 'tests');
  if (!existsSync(dir) || !statSync(dir).isDirectory()) return null;
  let n = 0;
  walkDir(dir, (f) => { if (f.endsWith('.test.mjs')) n++; });
  return n;
}

/**
 * Build the surface-count descriptor table for the given vault. `hookCounts`
 * is computed once and shared by the two hook surfaces. Each descriptor's
 * `actual` is resolved eagerly so a single drift pass can skip null surfaces.
 *
 * `command-count` keeps its original id + message phrasing for back-compat with
 * the result.command_count field and existing tests; the four new surfaces
 * follow the same shape.
 */
function buildSurfaceDescriptors(vaultDir, commandsDir) {
  const hookCounts = readHookCounts(vaultDir);
  return [
    {
      id: 'command-count',
      noun: 'commands',
      actual: (() => {
        const dir = commandsDir || join(vaultDir, 'commands');
        if (!existsSync(dir) || !statSync(dir).isDirectory()) return null;
        return readdirSync(dir).filter((f) => f.endsWith('.md') && !f.startsWith('.')).length;
      })(),
      // "8 commands", "8 /commands", "8 slash commands"
      claimRe: /\b(\d+)\s+(?:\/)?commands?\b/gi,
      skipMsg: 'command-count: no commands/ directory found (use --commands-dir to override)',
    },
    {
      id: 'skill-count',
      noun: 'skills',
      actual: countSkills(vaultDir),
      // "40 skills", "40 user-facing skills"
      claimRe: /\b(\d+)\s+(?:user-facing\s+)?skills?\b/gi,
      skipMsg: 'skill-count: no skills/ directory found',
    },
    {
      id: 'agent-count',
      noun: 'agents',
      actual: countAgents(vaultDir),
      // "14 sub-agent definitions" / "14 sub-agents" / "14 agent definitions"
      // Deliberately NOT matched: "3 agent role definitions" (Codex-specific).
      claimRe: /\b(\d+)\s+(?:sub-agents?|agent\s+definitions?)\b/gi,
      skipMsg: 'agent-count: no agents/ directory found',
    },
    {
      id: 'hook-event-count',
      noun: 'distinct hook events',
      actual: hookCounts ? hookCounts.events : null,
      // "10 distinct events"
      claimRe: /\b(\d+)\s+distinct\s+events?\b/gi,
      skipMsg: 'hook-event-count: no hooks/hooks.json found or unparseable',
    },
    {
      id: 'hook-matcher-count',
      noun: 'hook matcher entries',
      actual: hookCounts ? hookCounts.matchers : null,
      // "14 matcher entries"
      claimRe: /\b(\d+)\s+matcher\s+entries\b/gi,
      skipMsg: 'hook-matcher-count: no hooks/hooks.json found or unparseable',
    },
    {
      id: 'test-count',
      noun: 'test files',
      actual: countTestFiles(vaultDir),
      // "N test files" — the README badge claims a runtime PASS count
      // ("9303 tests"), which a static checker cannot derive, so we match only
      // the explicit file-count phrasing. No doc claims this today → skipped.
      claimRe: /\b(\d+)\s+test\s+files?\b/gi,
      skipMsg: 'test-count: no tests/ directory found',
    },
  ];
}

const REPO_SHAPE_RE = /^[A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)+$/;

function detectRepo(vaultDir) {
  const url = execFileSync('git', ['remote', 'get-url', 'origin'], { cwd: vaultDir, encoding: 'utf8' }).trim();
  const m = /[:/]([^:/\s]+\/[^/\s]+?)(?:\.git)?$/.exec(url);
  const candidate = m ? m[1] : null;
  return candidate && REPO_SHAPE_RE.test(candidate) ? candidate : null;
}

function hasGlab() {
  try {
    execFileSync('sh', ['-c', 'command -v glab'], { stdio: 'pipe' });
    return true;
  } catch { return false; }
}

function lookupIssueState(iid, repo, cache) {
  if (cache.has(iid)) return cache.get(iid);
  let state = 'unknown';
  try {
    const out = execFileSync('glab', ['issue', 'view', iid, '--repo', repo], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    const m = /^state:\s*(open|closed)/im.exec(out);
    if (m) state = m[1];
  } catch { /* glab returned non-zero — leave as unknown */ }
  cache.set(iid, state);
  return state;
}

// ───────────────────────────────────────────────────────────────────────────
// Rule-scoping family (Check 9) — validates .claude/rules/*.md frontmatter
// against the scripts/lib/rule-loader.mjs contract:
//   1. paths-presence   → errors[]:   a top-level `paths:` key (rule-loader.mjs
//      only recognises `globs:`; `paths:` silently loads the rule ALWAYS-ON).
//   2. cited-but-missing → errors[]:  (a) `.claude/rules/<name>.md` citations in
//      CLAUDE.md/AGENTS.md that don't exist on disk; (b) bare `<name>.md`
//      tokens in a rule's own `## See Also` footer that don't exist on disk
//      (tokens carrying a path separator are cross-directory references and
//      out of scope).
//   3. zero-match-globs → warnings[]: a `globs:` pattern matching 0 tracked
//      files (git ls-files). WARN, not error — library/exemplar repos may
//      legitimately carry dead stack rules.
//   4. foreign-glob     → warnings[]: a glob pattern containing a PascalCase
//      product-like token (e.g. `WalkAITalkieTests`) — a likely copy-paste
//      leftover from another project's rule.
//   5. unreadable-file  → warnings[]: a rule file that could not be read
//      (permissions, race with a concurrent delete, etc.) — surfaced instead
//      of being silently skipped, since a completeness audit that silently
//      drops files defeats its purpose. WARN, not error — an unreadable file
//      must not brick the gate under `mode: hard`.
// ───────────────────────────────────────────────────────────────────────────

let _picomatchRuleScoping = null;
function getPicomatchForRuleScoping() {
  if (_picomatchRuleScoping !== null) return _picomatchRuleScoping;
  try {
    const require = createRequire(import.meta.url);
    _picomatchRuleScoping = require('picomatch');
  } catch {
    _picomatchRuleScoping = false;
  }
  return _picomatchRuleScoping;
}

/** Minimal glob-to-RegExp fallback (mirrors scripts/lib/rule-loader.mjs),
 * used only when picomatch is unavailable in node_modules. */
function globToRegExpFallback(pattern) {
  const p = pattern.replace(/\\/g, '/');
  let re = '';
  let i = 0;
  while (i < p.length) {
    const c = p[i];
    if (c === '*' && p[i + 1] === '*') {
      re += '.*';
      i += 2;
      if (p[i] === '/') i++;
    } else if (c === '*') {
      re += '[^/]*';
      i++;
    } else if (c === '?') {
      re += '[^/]';
      i++;
    } else if (c === '.') {
      re += '\\.';
      i++;
    } else {
      re += c.replace(/[$()+[\]^{|}]/g, '\\$&');
      i++;
    }
  }
  return new RegExp(`^${re}$`);
}

/** Returns true when `pattern` matches at least one entry in `trackedFiles`. */
function globMatchesAny(pattern, trackedFiles) {
  const pm = getPicomatchForRuleScoping();
  if (pm) {
    return trackedFiles.some((f) => pm.isMatch(f, pattern, { dot: true }));
  }
  const re = globToRegExpFallback(pattern);
  return trackedFiles.some((f) => re.test(f));
}

/**
 * Returns the repo's tracked files (relative, forward-slash separated) via
 * `git ls-files`; falls back to a manual walk (excluding dotdirs and
 * node_modules — same exclusions as `walkDir`) when git is unavailable.
 */
function listTrackedFiles(vaultDir) {
  try {
    const out = execFileSync('git', ['ls-files'], { cwd: vaultDir, encoding: 'utf8' });
    return out.split('\n').filter(Boolean);
  } catch {
    const files = [];
    walkDir(vaultDir, (f) => files.push(relative(vaultDir, f).replace(/\\/g, '/')));
    return files;
  }
}

const RULE_HEADER_LINE_RE = /^[ \t]*(?:<!--.*-->)?[ \t]*$/;

function stripLeadingRuleHeaderLines(content) {
  const lines = content.split(/\r?\n/);
  let idx = 0;
  while (idx < lines.length && RULE_HEADER_LINE_RE.test(lines[idx])) idx++;
  return lines.slice(idx).join('\n');
}

/** Extracts the raw frontmatter block body (text between the `---` delimiters),
 * or null when the file has no frontmatter block. Leading blank/comment
 * provenance lines are tolerated so Check 9 sees the same frontmatter shape
 * that rule-loader.mjs accepts. */
function extractFrontmatterBlockBody(content) {
  const m = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(stripLeadingRuleHeaderLines(content));
  return m ? m[1] : null;
}

/** PascalCase product-like token check (e.g. `WalkAITalkieTests`) — the
 * foreign-glob probe's discriminator, per Check 9 spec. */
const FOREIGN_GLOB_TOKEN_RE = /[A-Z][a-z]+[A-Z]/;

/**
 * Extracts bare `<name>.md` tokens from a "## See Also" footer's body lines,
 * skipping any token that carries a path separator (cross-directory
 * references are out of scope) or is not shaped like a kebab-case rule
 * filename. Returns `[{ token, lineOffset }]`, `lineOffset` 0-based relative
 * to `bodyLines[0]`.
 */
function extractSeeAlsoTokens(bodyLines) {
  const results = [];
  for (let i = 0; i < bodyLines.length; i++) {
    const rawTokens = bodyLines[i].split(/[\s·]+/).filter(Boolean);
    for (const raw of rawTokens) {
      const stripped = raw.replace(/^[`[(]+/, '').replace(/[`\]),.;:]+$/, '');
      if (!/\.md$/.test(stripped)) continue;
      if (stripped.includes('/')) continue; // cross-directory reference — out of scope
      if (!/^[a-z][a-z0-9-]*\.md$/.test(stripped)) continue; // not kebab-case rule-filename shaped
      results.push({ token: stripped, lineOffset: i });
    }
  }
  return results;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const vaultDir = resolve(process.env.VAULT_DIR || process.cwd());

  if (!['strict', 'hard', 'warn', 'off'].includes(args.mode)) {
    process.stderr.write(`{"status":"infra-error","reason":"invalid --mode: ${args.mode}"}\n`);
    process.exit(2);
  }
  // `hard` is a legacy alias for `strict` (#217 enum migration — parity with
  // the vault-sync validator, which normalizes the reverse direction). Collapse
  // to a single blocking value so exactly one internal value flows downstream.
  if (args.mode === 'hard') args.mode = 'strict';

  // Alias-aware instruction file resolution (issue #33).
  // CLAUDE.md (Claude Code / Cursor IDE) and AGENTS.md (Codex CLI) are
  // transparent aliases — see skills/_shared/instruction-file-resolution.md.
  const instr = resolveInstructionFile(vaultDir); // {path, kind} | null
  const resolvedPath = instr ? instr.path : null;
  const resolvedKind = instr ? instr.kind : null;

  if (args.mode === 'off') {
    process.stdout.write(JSON.stringify({
      status: 'skipped-mode-off', mode: 'off', vault_dir: vaultDir,
      resolved_path: resolvedPath, resolved_kind: resolvedKind,
    }) + '\n');
    process.exit(0);
  }

  if (!existsSync(vaultDir) || !statSync(vaultDir).isDirectory()) {
    process.stderr.write(`{"status":"infra-error","reason":"VAULT_DIR does not exist: ${vaultDir}"}\n`);
    process.exit(2);
  }

  // Seed default includePaths post-vaultDir resolution (alias-aware).
  if (args.includePaths.length === 0) {
    args.includePaths = [
      ...(instr ? [relative(vaultDir, instr.path)] : []),
      '_meta/**/*.md',
    ];
  }

  const scopeFiles = resolveScopeFiles(vaultDir, args.includePaths);
  const checksSkipped = [];

  let actualProjectCount = null;
  if (!args.skipProjectCount) {
    const projectsDir = join(vaultDir, '01-projects');
    if (existsSync(projectsDir) && statSync(projectsDir).isDirectory()) {
      actualProjectCount = readdirSync(projectsDir, { withFileTypes: true })
        .filter((e) => e.isDirectory() && !e.name.startsWith('_') && !e.name.startsWith('.'))
        .length;
    } else {
      checksSkipped.push('project-count-sync: no 01-projects/ directory at vault root');
    }
  }

  // Check 5: surface-count family (command/skill/agent/hook-event/hook-matcher/
  // test). Each surface derives an ACTUAL on-disk count and compares it to a
  // CLAIMED count regex-extracted from any scanned doc. Surfaces whose source
  // artifact is absent (actual === null) are skipped; surfaces the doc never
  // claims are skipped per-line in the scan loop (no claim invented).
  // `--skip-surface-count` disables the whole family; `--skip-command-count`
  // remains a back-compat alias that disables only the command-count surface.
  const commandsDir = args.commandsDir ? resolve(args.commandsDir) : null;
  let surfaces = [];
  if (!args.skipSurfaceCount) {
    surfaces = buildSurfaceDescriptors(vaultDir, commandsDir);
    if (args.skipCommandCount) {
      surfaces = surfaces.filter((s) => s.id !== 'command-count');
    }
    for (const s of surfaces) {
      if (s.actual === null) checksSkipped.push(s.skipMsg);
    }
  }
  // Active surfaces = family enabled AND source artifact present on disk.
  const activeSurfaces = surfaces.filter((s) => s.actual !== null);
  // Back-compat: the command-count surface's actual feeds result.command_count.
  const commandSurface = activeSurfaces.find((s) => s.id === 'command-count');
  const actualCommandCount = commandSurface ? commandSurface.actual : null;

  let repo = args.repo;
  const glabPresent = !args.skipIssueRefs && hasGlab();
  if (!args.skipIssueRefs && !glabPresent) {
    checksSkipped.push('issue-reference-freshness: glab not found in PATH');
  }
  if (!args.skipIssueRefs && glabPresent && !repo) {
    try { repo = detectRepo(vaultDir); } catch { /* ignore */ }
    if (!repo) checksSkipped.push('issue-reference-freshness: could not detect origin repo (use --repo)');
  }
  const runIssueCheck = !args.skipIssueRefs && glabPresent && !!repo;

  const checksRun = [];
  if (!args.skipPathResolver) checksRun.push('path-resolver');
  if (!args.skipProjectCount && actualProjectCount !== null) checksRun.push('project-count-sync');
  if (runIssueCheck) checksRun.push('issue-reference-freshness');
  if (!args.skipSessionFiles) checksRun.push('session-file-existence');
  for (const s of activeSurfaces) checksRun.push(s.id);

  const errors = [];
  const warnings = [];
  const issueCache = new Map();

  // Check 6: session-config-parity (issue #30) — diff top-level keys under
  // `## Session Config` between the canonical template and the local
  // instruction file.
  //
  // Severity split (issue #785 follow-up — coordinator triage of the initial
  // #785 fix): a missing MANDATORY key (present in the template's "Full
  // minimal baseline" — the 7 schema-enforced keys) is an ERROR. A missing
  // OPT-IN key (present only in the "Full opt-in baseline" — i.e. NOT in the
  // minimal block) is a WARNING, not an error: a consumer repo that
  // legitimately does not adopt an opt-in feature (e.g. no `handover-gate`)
  // must not go red — this repo's own CLAUDE.md deliberately omits 37
  // opt-in-baseline keys. `mode: hard` only exits non-zero on `errors[]`, so
  // pure opt-in gaps never block `autonomous-gated` skill-evolution's
  // `runConfigValidationGate()`.
  //
  // This is a deliberate, coordinator-directed DEVIATION from #785's literal
  // fix-direction ("plants an opt-in key... asserts a session-config-parity
  // ERROR") — the mechanism (union template keys via `{ occurrence: 'last' }`)
  // is unchanged, but the missing-opt-in-key case now lands in `warnings[]`
  // instead of `errors[]`. Local keys unknown to the template union were
  // (and remain) never flagged in either direction — no existing code path
  // inspected that direction before this change either.
  let configParityRan = false;
  if (!args.skipSessionConfigParity) {
    const templatePath = args.configTemplate
      ? resolve(args.configTemplate)
      : join(vaultDir, 'docs', 'session-config-template.md');
    if (!instr) {
      checksSkipped.push('session-config-parity: no instruction file');
    } else if (!existsSync(templatePath) || !statSync(templatePath).isFile()) {
      checksSkipped.push('session-config-parity: no docs/session-config-template.md found');
    } else {
      const templateContent = readFileSync(templatePath, 'utf8');
      const localContent = readFileSync(instr.path, 'utf8');
      // 'last' occurrence reaches the "Full opt-in baseline" block (the full
      // key catalog, a strict superset of the minimal block) — issue #785.
      // 'first' occurrence reaches the "Full minimal baseline" (7 mandatory
      // keys) — used here to classify which missing keys are mandatory vs
      // opt-in. When the template has only ONE `## Session Config` heading
      // (e.g. a test fixture, or a repo that never split the two baselines),
      // 'first' and 'last' resolve to the SAME block, so every key is
      // treated as mandatory — preserving pre-existing behaviour for
      // single-block templates.
      const tplBlock = extractSessionConfigBlock(templateContent, { occurrence: 'last' });
      const tplMinimalBlock = extractSessionConfigBlock(templateContent, { occurrence: 'first' });
      const localBlock = extractSessionConfigBlock(localContent);
      if (!tplBlock) {
        checksSkipped.push('session-config-parity: template has no ## Session Config block');
      } else {
        configParityRan = true;
        const tplKeys = extractTopLevelKeys(tplBlock.body);
        const tplMinimalKeys = new Set(tplMinimalBlock ? extractTopLevelKeys(tplMinimalBlock.body) : []);
        const localKeys = new Set(localBlock ? extractTopLevelKeys(localBlock.body) : []);
        // Absent local block: line 1 (nothing to anchor to); present local
        // block: attribute to its own heading line — same as before #785.
        const rel = relative(vaultDir, instr.path);
        const line = localBlock ? localBlock.headingLine : 1;
        const missing = tplKeys.filter((k) => !localKeys.has(k));
        for (const key of missing) {
          if (tplMinimalKeys.has(key)) {
            errors.push({
              check: 'session-config-parity', file: rel, line,
              message: `Session Config missing top-level key '${key}' (present in docs/session-config-template.md)`,
              extracted: key,
            });
          } else {
            warnings.push({
              check: 'session-config-parity', file: rel, line,
              message: `Session Config omits opt-in top-level key '${key}' (documented in docs/session-config-template.md's opt-in baseline; not required)`,
              extracted: key,
            });
          }
        }
      }
    }
  } else {
    checksSkipped.push('session-config-parity: explicitly skipped');
  }
  if (configParityRan) checksRun.push('session-config-parity');

  // Check 7: vault-dir-parity (issue #600) — when BOTH instruction files
  // (CLAUDE.md AND AGENTS.md) exist as transparent aliases, they must agree on
  // `vault-integration.vault-dir`. A sibling project carried a dead vault-dir in
  // AGENTS.md for weeks while CLAUDE.md was correct; resolveInstructionFile()
  // picks only one file, so the disagreement went undetected. This check reads
  // both files independently and flags any divergence.
  let vaultDirParityRan = false;
  if (!args.skipVaultDirParity) {
    const claudePath = join(vaultDir, 'CLAUDE.md');
    const agentsPath = join(vaultDir, 'AGENTS.md');
    const claudeExists = existsSync(claudePath) && statSync(claudePath).isFile();
    const agentsExists = existsSync(agentsPath) && statSync(agentsPath).isFile();

    if (!claudeExists || !agentsExists) {
      checksSkipped.push('vault-dir-parity: requires both CLAUDE.md and AGENTS.md (only one present)');
    } else {
      const claudeVi = readVaultIntegration(claudePath);
      const agentsVi = readVaultIntegration(agentsPath);
      if (!claudeVi.present && !agentsVi.present) {
        checksSkipped.push('vault-dir-parity: neither file has a vault-integration: block');
      } else {
        vaultDirParityRan = true;
        const claudeDir = claudeVi.vaultDir;
        const agentsDir = agentsVi.vaultDir;
        if (claudeDir !== agentsDir) {
          errors.push({
            check: 'vault-dir-parity', file: 'AGENTS.md', line: 1,
            message: `vault-integration.vault-dir disagrees between instruction files: CLAUDE.md='${claudeDir ?? '(unset)'}' vs AGENTS.md='${agentsDir ?? '(unset)'}'`,
            extracted: agentsDir ?? '(unset)',
          });
        }
      }
    }
  } else {
    checksSkipped.push('vault-dir-parity: explicitly skipped');
  }
  if (vaultDirParityRan) checksRun.push('vault-dir-parity');

  // Check 8: generated-rule-staleness (WARN-mode, advisory — Epic #693 FA4 #697).
  // For each .claude/rules/*.md with frontmatter `auto-generated: true`, extract
  // `learning-key` and verify it matches a non-expired entry in
  // `.orchestrator/metrics/learnings.jsonl`.
  //
  // Key derivation mirrors emitter.mjs `toActivationMetadata`:
  //   learningKey = `${type}/${kebab(title || subject || '')}`
  //   kebab(s) = s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  //
  // WARN (never error) when:
  //   - learnings.jsonl is present AND no entry's derived key matches the rule's
  //     `learning-key` (absent learning), OR
  //   - the matching entry's `expires_at` < now (expired learning).
  // When learnings.jsonl is absent, every key counts as absent — warn on each
  // generated rule's key.
  // The check is silently skipped (no id pushed) when .claude/rules/ is absent
  // or contains no .md files with auto-generated: true.
  if (!args.skipGeneratedRuleStaleness) {
    (function runGeneratedRuleStaleness() {
    const rulesDir = join(vaultDir, '.claude', 'rules');
    if (!existsSync(rulesDir) || !statSync(rulesDir).isDirectory()) return;

    // Minimal inline frontmatter extractor for auto-generated + learning-key.
    // Reads the opening --- ... --- block from a markdown file.
    function extractFrontmatterFields(mdContent) {
      const m = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(stripLeadingRuleHeaderLines(mdContent));
      if (!m) return { autoGenerated: false, learningKey: null, expiresAt: null };
      const block = m[1];
      const autoGenM = /^auto-generated:\s*(.+)$/m.exec(block);
      const learningKeyM = /^learning-key:\s*(.+)$/m.exec(block);
      const expiresAtM = /^expires-at:\s*(.+)$/m.exec(block);
      return {
        autoGenerated: autoGenM ? autoGenM[1].trim() === 'true' : false,
        learningKey: learningKeyM ? learningKeyM[1].trim() : null,
        expiresAt: expiresAtM ? expiresAtM[1].trim() : null,
      };
    }

    // Collect all .md files in .claude/rules/ with auto-generated: true.
    const ruleFiles = readdirSync(rulesDir)
      .filter((f) => f.endsWith('.md') && !f.startsWith('.'))
      .map((f) => join(rulesDir, f))
      .filter((absPath) => statSync(absPath).isFile());

    const generatedRules = [];
    for (const absPath of ruleFiles) {
      let content;
      try { content = readFileSync(absPath, 'utf8'); } catch { continue; }
      const fields = extractFrontmatterFields(content);
      if (!fields.autoGenerated) continue;
      generatedRules.push({
        absPath,
        relPath: relative(vaultDir, absPath),
        learningKey: fields.learningKey,
        expiresAt: fields.expiresAt,
      });
    }

    // No generated rules found → silently skip (don't push the check id).
    if (generatedRules.length === 0) return;

    // Slugify function mirroring emitter.mjs `kebab()`.
    const kebab = (s) =>
      String(s)
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');

    // Build the set of known learning keys from learnings.jsonl.
    // key → expires_at (ISO string or null)
    const knownKeys = new Map();
    const learningsPath = join(vaultDir, '.orchestrator', 'metrics', 'learnings.jsonl');
    const learningsPresent = existsSync(learningsPath) && statSync(learningsPath).isFile();

    if (learningsPresent) {
      let raw;
      try { raw = readFileSync(learningsPath, 'utf8'); } catch { /* leave knownKeys empty */ }
      if (raw) {
        for (const line of raw.split('\n')) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          let entry;
          try { entry = JSON.parse(trimmed); } catch { continue; }
          if (!entry || typeof entry !== 'object') continue;
          const type = typeof entry.type === 'string' ? entry.type : '';
          const subjectOrTitle =
            (typeof entry.title === 'string' && entry.title !== '' ? entry.title : '') ||
            (typeof entry.subject === 'string' && entry.subject !== '' ? entry.subject : '');
          if (!type || !subjectOrTitle) continue;
          const derivedKey = `${type}/${kebab(subjectOrTitle)}`;
          // Store the most-recent expires_at (later entries overwrite earlier ones
          // with the same key — safe; duplicates are rare and same-key learnings
          // share the same expiry semantics).
          knownKeys.set(derivedKey, entry.expires_at ?? null);
        }
      }
    }

    const nowMs = Date.now();

    for (const rule of generatedRules) {
      const { relPath, learningKey, expiresAt } = rule;

      // If we cannot evaluate the key (no learning-key frontmatter), skip
      // silently — avoid false positives on malformed rules.
      if (!learningKey) continue;

      if (!learningsPresent || !knownKeys.has(learningKey)) {
        // Learning is absent from learnings.jsonl (or the file is missing entirely).
        warnings.push({
          check: 'generated-rule-staleness',
          file: relPath,
          line: 1,
          message: `Auto-generated rule references learning-key '${learningKey}' which is absent from .orchestrator/metrics/learnings.jsonl`,
          extracted: learningKey,
        });
        continue;
      }

      // Learning exists — check expiry.
      const storedExpiresAt = knownKeys.get(learningKey);
      // Prefer the frontmatter expires-at on the rule file; fall back to the
      // stored expires_at from the learning entry (both should agree, but the
      // rule file is authoritative for its own expiry).
      const expiryStr = expiresAt ?? storedExpiresAt;
      if (expiryStr) {
        const expiryMs = Date.parse(expiryStr);
        if (Number.isFinite(expiryMs) && expiryMs < nowMs) {
          warnings.push({
            check: 'generated-rule-staleness',
            file: relPath,
            line: 1,
            message: `Auto-generated rule's learning '${learningKey}' expired on ${expiryStr} (rule should be reviewed or removed)`,
            extracted: learningKey,
          });
        }
      }
    }

    // Push the check id only when ≥1 generated rule was scanned.
    checksRun.push('generated-rule-staleness');
    })();
  } else {
    checksSkipped.push('generated-rule-staleness: explicitly skipped');
  }

  // Check 9: rule-scoping — validates .claude/rules/*.md frontmatter against
  // the rule-loader.mjs contract (see the doc-comment above the helper
  // functions for the five probes, incl. unreadable-file). Silently skipped (no id pushed, no
  // checksSkipped entry) when .claude/rules/ is absent — mirrors Check 8's
  // silent-skip semantics. `--skip-rule-scoping` disables the whole check.
  if (!args.skipRuleScoping) {
    (function runRuleScoping() {
      const rulesDir = join(vaultDir, '.claude', 'rules');
      if (!existsSync(rulesDir) || !statSync(rulesDir).isDirectory()) return;

      checksRun.push('rule-scoping');

      const ruleFileNames = readdirSync(rulesDir)
        .filter((f) => f.endsWith('.md') && !f.startsWith('.'))
        .filter((f) => statSync(join(rulesDir, f)).isFile());
      const ruleFileSet = new Set(ruleFileNames);

      // Lazily computed — only needed once any rule declares ≥1 glob pattern.
      let trackedFiles = null;

      for (const fname of ruleFileNames) {
        const absPath = join(rulesDir, fname);
        const relPath = relative(vaultDir, absPath);
        let content;
        try {
          content = readFileSync(absPath, 'utf8');
        } catch (err) {
          warnings.push({
            check: 'rule-scoping', file: relPath, line: 1,
            message: `rule file unreadable — skipped from rule-scoping analysis (${err.code || err.message})`,
            extracted: fname,
          });
          continue;
        }

        // --- Probe 1: paths-presence → errors[] ---
        const fmBody = extractFrontmatterBlockBody(content);
        if (fmBody && /^paths:/m.test(fmBody)) {
          errors.push({
            check: 'rule-scoping', file: relPath, line: 1,
            message: `Rule frontmatter declares 'paths:' which rule-loader.mjs does not recognise — the rule silently loads ALWAYS-ON regardless of file scope. Migrate to 'globs:'.`,
            extracted: 'paths:',
          });
        }

        // --- Probes 3 & 4: zero-match-globs / foreign-glob → warnings[] ---
        let parsed;
        try { parsed = parseGlobsFrontmatter(content); } catch { parsed = { globs: null, meta: {} }; }
        const globs = parsed.globs;
        if (Array.isArray(globs) && globs.length > 0) {
          if (trackedFiles === null) trackedFiles = listTrackedFiles(vaultDir);
          for (const pattern of globs) {
            if (!globMatchesAny(pattern, trackedFiles)) {
              warnings.push({
                check: 'rule-scoping', file: relPath, line: 1,
                message: `glob '${pattern}' matches 0 tracked files (library/exemplar repos may legitimately carry dead stack rules)`,
                extracted: pattern,
              });
            }
            if (FOREIGN_GLOB_TOKEN_RE.test(pattern)) {
              warnings.push({
                check: 'rule-scoping', file: relPath, line: 1,
                message: `glob '${pattern}' contains a PascalCase product-like token — verify this rule was not copy-pasted from another project`,
                extracted: pattern,
              });
            }
          }
        }

        // --- Probe 2b: cited-but-missing (this rule's own "## See Also" footer) → errors[] ---
        const lines = content.split('\n');
        let seeAlsoStart = -1;
        for (let i = 0; i < lines.length; i++) {
          if (/^##\s+See Also\s*$/i.test(lines[i])) { seeAlsoStart = i + 1; break; }
        }
        if (seeAlsoStart !== -1) {
          let seeAlsoEnd = lines.length;
          for (let i = seeAlsoStart; i < lines.length; i++) {
            if (/^#{1,6}\s+/.test(lines[i])) { seeAlsoEnd = i; break; }
          }
          const bodyLines = lines.slice(seeAlsoStart, seeAlsoEnd);
          for (const { token, lineOffset } of extractSeeAlsoTokens(bodyLines)) {
            if (!ruleFileSet.has(token)) {
              errors.push({
                check: 'rule-scoping', file: relPath, line: seeAlsoStart + lineOffset + 1,
                message: `'## See Also' cites '${token}' which does not exist in .claude/rules/`,
                extracted: token,
              });
            }
          }
        }
      }

      // --- Probe 2a: cited-but-missing (CLAUDE.md / AGENTS.md citations) → errors[] ---
      for (const instrName of ['CLAUDE.md', 'AGENTS.md']) {
        const filePath = join(vaultDir, instrName);
        if (!existsSync(filePath) || !statSync(filePath).isFile()) continue;
        const fcontent = readFileSync(filePath, 'utf8');
        const flines = fcontent.split('\n');
        const citeRe = /\.claude\/rules\/([A-Za-z0-9_-]+\.md)\b/g;
        for (let i = 0; i < flines.length; i++) {
          citeRe.lastIndex = 0;
          let m;
          while ((m = citeRe.exec(flines[i])) !== null) {
            const cited = m[1];
            if (!ruleFileSet.has(cited)) {
              errors.push({
                check: 'rule-scoping', file: instrName, line: i + 1,
                message: `References .claude/rules/${cited} which does not exist on disk`,
                extracted: cited,
              });
            }
          }
        }
      }
    })();
  } else {
    checksSkipped.push('rule-scoping: explicitly skipped');
  }

  // Check 10: docs-parity (issue #780) — three sub-checks over the public docs
  // surface, silently skipped (no checksRun push, no checksSkipped entry) when
  // docs/components.md is absent (mirrors Check 8/9's silent-skip semantics):
  //   (a) count-claims — docs/components.md's own heading counts ("## Skills
  //       (N user-facing)", "## Commands (N)", "## Agents (N typed
  //       sub-agents)", "## Hook event types (N)") vs the SAME actual on-disk
  //       derivation the surface-count family (Check 5) uses (countSkills /
  //       the commands-dir listing / countAgents / readHookCounts). This does
  //       NOT reuse the surface-count family's `claimRe` regexes — those are
  //       tuned for CLAUDE.md/README prose phrasing ("40 skills", "8 distinct
  //       events") and verifiably do not match components.md's own heading
  //       convention (count precedes/follows the noun differently); reusing
  //       them verbatim would silently never fire. New regexes tailored to
  //       the doc's actual authored structure are used instead.
  //   (b) config-block-parity — top-level Session Config keys documented in
  //       docs/session-config-template.md (opt-in baseline, via the Part 1
  //       'last'-occurrence extractor) vs mentioned anywhere in
  //       docs/session-config-reference.md (`extractDocKeyMentions` — yaml
  //       fences, headings, and markdown-table first-cell keys; see its
  //       doc-comment for why a naive fence-only extraction under-counts).
  //   (c) metrics-path-liveness — stale `.claude/metrics/` path references
  //       (canonical path is `.orchestrator/metrics/`) in root `docs/*.md` or
  //       `docs/examples/*.md`.
  // `--skip-docs-parity` disables the whole check.
  if (!args.skipDocsParity) {
    (function runDocsParity() {
      const componentsPath = join(vaultDir, 'docs', 'components.md');
      if (!existsSync(componentsPath) || !statSync(componentsPath).isFile()) return; // silent skip

      checksRun.push('docs-parity');
      const componentsRel = relative(vaultDir, componentsPath);
      const componentsContent = readFileSync(componentsPath, 'utf8');
      const componentsLines = componentsContent.split('\n');

      // --- Sub-check (a): count-claims ---
      const docsParitySurfaces = [
        {
          noun: 'skills',
          actual: countSkills(vaultDir),
          re: /^##\s+Skills\s+\((\d+)\s+user-facing\)/i,
        },
        {
          noun: 'commands',
          actual: (() => {
            const dir = commandsDir || join(vaultDir, 'commands');
            if (!existsSync(dir) || !statSync(dir).isDirectory()) return null;
            return readdirSync(dir).filter((f) => f.endsWith('.md') && !f.startsWith('.')).length;
          })(),
          re: /^##\s+Commands\s+\((\d+)\)/i,
        },
        {
          noun: 'agents',
          actual: countAgents(vaultDir),
          re: /^##\s+Agents\s+\((\d+)\s+typed\s+sub-agents\)/i,
        },
        {
          noun: 'distinct hook events',
          actual: (() => {
            const hc = readHookCounts(vaultDir);
            return hc ? hc.events : null;
          })(),
          re: /^##\s+Hook\s+event\s+types\s+\((\d+)\)/i,
        },
      ];
      for (let i = 0; i < componentsLines.length; i++) {
        const line = componentsLines[i];
        for (const surface of docsParitySurfaces) {
          if (surface.actual === null) continue; // artifact absent — nothing to compare
          const m = surface.re.exec(line);
          if (m) {
            const claimed = parseInt(m[1], 10);
            if (claimed !== surface.actual) {
              errors.push({
                check: 'docs-parity', file: componentsRel, line: i + 1,
                message: `docs/components.md claims ${claimed} ${surface.noun} but actual on-disk count is ${surface.actual}`,
                extracted: m[0],
              });
            }
          }
        }
      }

      // --- Sub-check (b): config-block-parity ---
      const templatePathForDocsParity = join(vaultDir, 'docs', 'session-config-template.md');
      const referencePath = join(vaultDir, 'docs', 'session-config-reference.md');
      if (
        existsSync(templatePathForDocsParity) && statSync(templatePathForDocsParity).isFile() &&
        existsSync(referencePath) && statSync(referencePath).isFile()
      ) {
        const templateContentForDocsParity = readFileSync(templatePathForDocsParity, 'utf8');
        const referenceContent = readFileSync(referencePath, 'utf8');
        const tplBlockForDocsParity = extractSessionConfigBlock(templateContentForDocsParity, { occurrence: 'last' });
        if (tplBlockForDocsParity) {
          const tplKeysForDocsParity = extractTopLevelKeys(tplBlockForDocsParity.body);
          const refKeys = extractDocKeyMentions(referenceContent);
          const referenceRel = relative(vaultDir, referencePath);
          for (const key of tplKeysForDocsParity) {
            if (!refKeys.has(key)) {
              errors.push({
                check: 'docs-parity', file: referenceRel, line: 1,
                message: `Session Config key '${key}' (documented in docs/session-config-template.md) is not documented in docs/session-config-reference.md`,
                extracted: key,
              });
            }
          }
        }
      }

      // --- Sub-check (c): metrics-path-liveness ---
      const docsDir = join(vaultDir, 'docs');
      const metricsScanTargets = [];
      if (existsSync(docsDir) && statSync(docsDir).isDirectory()) {
        for (const f of readdirSync(docsDir, { withFileTypes: true })) {
          if (f.isFile() && f.name.endsWith('.md')) metricsScanTargets.push(join(docsDir, f.name));
        }
        const examplesDir = join(docsDir, 'examples');
        if (existsSync(examplesDir) && statSync(examplesDir).isDirectory()) {
          for (const f of readdirSync(examplesDir, { withFileTypes: true })) {
            if (f.isFile() && f.name.endsWith('.md')) metricsScanTargets.push(join(examplesDir, f.name));
          }
        }
      }
      for (const abs of metricsScanTargets) {
        const rel = relative(vaultDir, abs);
        let content;
        try { content = readFileSync(abs, 'utf8'); } catch { continue; }
        const metricsLines = content.split('\n');
        for (let i = 0; i < metricsLines.length; i++) {
          if (metricsLines[i].includes('.claude/metrics/')) {
            errors.push({
              check: 'docs-parity', file: rel, line: i + 1,
              message: `Stale metrics path '.claude/metrics/' referenced — canonical path is '.orchestrator/metrics/'`,
              extracted: '.claude/metrics/',
            });
          }
        }
      }
    })();
  } else {
    checksSkipped.push('docs-parity: explicitly skipped');
  }

  if (scopeFiles.length === 0) {
    process.stdout.write(JSON.stringify({
      status: 'skipped', mode: args.mode, vault_dir: vaultDir,
      resolved_path: resolvedPath, resolved_kind: resolvedKind,
      files_scanned: 0, checks_run: checksRun, checks_skipped: checksSkipped,
      errors, warnings, reason: 'no scope files matched',
    }) + '\n');
    process.exit(errors.length > 0 && args.mode === 'strict' ? 1 : 0);
  }

  for (const abs of scopeFiles) {
    const rel = relative(vaultDir, abs);
    const content = readFileSync(abs, 'utf8');
    const lines = content.split('\n');

    let inFence = false;
    let currentSection = null;
    let currentSectionType = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineNum = i + 1;

      if (/^\s*```/.test(line)) { inFence = !inFence; continue; }

      const hmatch = /^(#{1,6})\s+(.+?)\s*$/.exec(line);
      if (hmatch && !inFence) {
        currentSection = hmatch[2];
        currentSectionType = classifySection(currentSection);
        continue;
      }

      if (!args.skipPathResolver && !inFence) {
        const pathRegex = /\/Users\/[A-Za-z0-9._/-]+/g;
        let m;
        while ((m = pathRegex.exec(line)) !== null) {
          const p = m[0].replace(/[.,;:)\]`"']+$/, '');
          if (!existsSync(p)) {
            errors.push({
              check: 'path-resolver', file: rel, line: lineNum,
              message: `Absolute path does not exist: ${p}`,
              extracted: p,
            });
          }
        }
      }

      if (!args.skipProjectCount && actualProjectCount !== null) {
        const countRegex = /\((\d+)\s+(registered|projects?|subfolders?)\)/gi;
        let m;
        while ((m = countRegex.exec(line)) !== null) {
          const claimed = parseInt(m[1], 10);
          if (claimed !== actualProjectCount) {
            errors.push({
              check: 'project-count-sync', file: rel, line: lineNum,
              message: `Hardcoded count claims ${claimed} ${m[2]} but actual 01-projects/ count is ${actualProjectCount}`,
              extracted: m[0],
            });
          }
        }
      }

      if (runIssueCheck && currentSectionType === 'forward' && !inFence) {
        const issueRegex = /#(\d+)\b/g;
        let m;
        while ((m = issueRegex.exec(line)) !== null) {
          const iid = m[1];
          const state = lookupIssueState(iid, repo, issueCache);
          if (state === 'closed') {
            errors.push({
              check: 'issue-reference-freshness', file: rel, line: lineNum,
              message: `Issue #${iid} is closed but referenced in forward-looking section "${currentSection}"`,
              extracted: `#${iid}`,
            });
          } else if (state === 'unknown') {
            warnings.push({
              check: 'issue-reference-freshness', file: rel, line: lineNum,
              message: `Could not resolve state of issue #${iid} via glab (may not exist or auth issue)`,
              extracted: `#${iid}`,
            });
          }
        }
      }

      if (!args.skipSessionFiles) {
        // Dual-read: tolerate both flat legacy `50-sessions/<id>.md` AND
        // per-repo namespaced `50-sessions/<repo>/<id>.md` (Issue #660).
        const sessionRegex = /50-sessions\/(?:([a-z0-9][a-z0-9-]*)\/)?(\d{4}-\d{2}-\d{2}-[a-z0-9-]+)\.md/g;
        let m;
        while ((m = sessionRegex.exec(line)) !== null) {
          const repo = m[1]; // optional repo segment (undefined if flat reference)
          const id = m[2];   // session date-slug
          let found = false;
          if (repo !== undefined) {
            // Namespaced reference: only check the specific namespaced path.
            found = existsSync(join(vaultDir, '50-sessions', repo, `${id}.md`));
          } else {
            // Flat reference: accept if the flat path exists OR if ANY per-repo
            // subfolder contains a file with the same id (migration tolerance).
            const flatPath = join(vaultDir, '50-sessions', `${id}.md`);
            if (existsSync(flatPath)) {
              found = true;
            } else {
              // Scan one level of subdirectories under 50-sessions/ for <id>.md.
              const sessionsDir = join(vaultDir, '50-sessions');
              try {
                const subdirs = readdirSync(sessionsDir, { withFileTypes: true })
                  .filter((e) => e.isDirectory())
                  .map((e) => e.name);
                found = subdirs.some((sub) =>
                  existsSync(join(sessionsDir, sub, `${id}.md`))
                );
              } catch {
                // sessionsDir does not exist or is unreadable — found stays false.
              }
            }
          }
          if (!found) {
            errors.push({
              check: 'session-file-existence', file: rel, line: lineNum,
              message: `Referenced session file does not exist: ${m[0]}`,
              extracted: m[0],
            });
          }
        }
      }

      // Surface-count family: one EXACT-count drift check per active surface.
      // A surface only fires when the doc makes an explicit numeric claim that
      // its regex matches; an unclaimed surface produces no errors (skip).
      for (const surface of activeSurfaces) {
        const re = surface.claimRe;
        re.lastIndex = 0; // reset shared /g/ regex before each line
        let m;
        while ((m = re.exec(line)) !== null) {
          const claimed = parseInt(m[1], 10);
          if (claimed !== surface.actual) {
            const err = {
              check: surface.id, file: rel, line: lineNum,
              message: `Narrative claims ${claimed} ${surface.noun} but actual on-disk count is ${surface.actual}`,
              extracted: m[0],
              count: { surface: surface.id, actual: surface.actual, claimed },
            };
            // Back-compat: the original command-count error also carried a
            // top-level `command_count` field; preserve it.
            if (surface.id === 'command-count') {
              err.command_count = { actual: surface.actual, claimed };
            }
            errors.push(err);
          }
        }
      }
    }
  }

  const status = errors.length === 0 ? 'ok' : 'invalid';
  const result = {
    status, mode: args.mode, vault_dir: vaultDir,
    resolved_path: resolvedPath, resolved_kind: resolvedKind,
    files_scanned: scopeFiles.length,
    checks_run: checksRun,
    checks_skipped: checksSkipped,
    errors, warnings,
  };
  if (actualCommandCount !== null) {
    result.command_count = { actual: actualCommandCount };
  }
  process.stdout.write(JSON.stringify(result) + '\n');

  process.exit(errors.length > 0 && args.mode === 'strict' ? 1 : 0);
}

main();
