/**
 * skills/discovery/probes/ssot-code-diff.mjs
 *
 * Probe: SSOT-vs-Code Diff — detects prose "count" claims in documentation
 * that have drifted from the actual code/filesystem constant they describe.
 * Docs are never the source of truth; the code (or a checked-in JSON/FS
 * layout) is. This is the mechanical follow-up to a fleet-mining finding
 * (conf 0.95): three prose sites (CLAUDE.md, .orchestrator/steering/structure.md,
 * skills/hook-development/SKILL.md) hardcode "(13 rules)" for
 * `.orchestrator/policy/blocked-commands.json` without any mechanical
 * re-check, and `claude-md-drift-check` Check 10 only covers claims bound to
 * `docs/components.md` — the gap is prose claims living anywhere else.
 *
 * Deliberately a CONSERVATIVE, hand-curated claim registry (v1) — not a
 * generic "any number near any noun" matcher, which would drown in false
 * positives. Each registry entry pairs one filesystem/JSON-derived "actual"
 * count with a narrow, targeted regex over a fixed small set of known doc
 * sources. Adding a new claim class means adding a new registry entry, not
 * loosening an existing regex.
 *
 * Registry v1 (four entries):
 *   1. `.orchestrator/policy/blocked-commands.json` rules.length vs.
 *      "(N rules)" / "N rules" claims — policy/security-relevant, severity high.
 *   2. `.claude/rules/*.md` file count (non-recursive) vs. "N rule files" claims.
 *   3. `skills/` user-facing directory count (excludes `_shared/`) vs.
 *      "N user-facing skills" / "N skills" claims.
 *   4. `commands/*.md` file count vs. "N slash-commands" / "N commands" claims.
 *
 * Scope exclusions: CHANGELOG.md, docs/adr/, docs/prd/, docs/retro/ are never
 * scanned — same principle as the docs-staleness probe (historical/immutable
 * documents are not "living" claims to re-verify).
 *
 * A missing "actual" source (e.g. blocked-commands.json absent) gracefully
 * skips claim-checking for that one registry entry only — it never throws
 * and never produces a spurious finding. A missing doc source is likewise
 * skipped per-file.
 *
 * Input: projectRoot (absolute path to the repo running discovery), config
 * (parsed Session Config object, may be empty/partial — this probe reads no
 * config keys; it activates whenever the docs-probe category is dispatched).
 *
 * Output: {findings[], metrics, duration_ms, [skipped_reason]}. Never throws.
 * Also appends one JSONL summary record to .orchestrator/metrics/ssot-code-diff.jsonl.
 */

import { existsSync, readdirSync, readFileSync, mkdirSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

// ---------------------------------------------------------------------------
// Doc source sets (deliberately small and hand-curated)
// ---------------------------------------------------------------------------

const SOURCE_SET_POLICY = [
  'CLAUDE.md',
  'AGENTS.md',
  join('.orchestrator', 'steering', 'structure.md'),
  join('skills', 'hook-development', 'SKILL.md'),
];

const SOURCE_SET_INVENTORY = [
  'README.md',
  join('docs', 'components.md'),
  join('.orchestrator', 'steering', 'structure.md'),
];

// ---------------------------------------------------------------------------
// "Actual" computers — each returns a number, or null when the underlying
// source is absent/unreadable (graceful skip, never throws upward).
// ---------------------------------------------------------------------------

function countBlockedCommandsRules(root) {
  const p = join(root, '.orchestrator', 'policy', 'blocked-commands.json');
  if (!existsSync(p)) return null;
  try {
    const json = JSON.parse(readFileSync(p, 'utf8'));
    return Array.isArray(json.rules) ? json.rules.length : null;
  } catch {
    return null;
  }
}

function countRuleFiles(root) {
  const dir = join(root, '.claude', 'rules');
  if (!existsSync(dir)) return null;
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    return entries.filter((e) => e.isFile() && e.name.endsWith('.md')).length;
  } catch {
    return null;
  }
}

function countUserFacingSkills(root) {
  const dir = join(root, 'skills');
  if (!existsSync(dir)) return null;
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    return entries.filter((e) => e.isDirectory() && e.name !== '_shared').length;
  } catch {
    return null;
  }
}

function countCommands(root) {
  const dir = join(root, 'commands');
  if (!existsSync(dir)) return null;
  try {
    const entries = readdirSync(dir, { withFileTypes: true });
    return entries.filter((e) => e.isFile() && e.name.endsWith('.md')).length;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Claim scanner — narrow, per-registry-entry regex over line-split content.
// ---------------------------------------------------------------------------

/**
 * @param {string} content        Full file content.
 * @param {RegExp|null} contextRe Non-global regex; if set, a line must match
 *                                 this BEFORE the value regex is applied
 *                                 (used to disambiguate e.g. "N rules" claims
 *                                 that must be about blocked-commands.json).
 * @param {RegExp} valueRe        Regex whose first capture group is the
 *                                 claimed integer. Applied per-line, global.
 * @returns {Array<{line:number, claimed:number, matchedText:string}>}
 */
function scanLinesForClaim(content, contextRe, valueRe) {
  const claims = [];
  const lines = content.split('\n');
  const flags = valueRe.flags.includes('g') ? valueRe.flags : valueRe.flags + 'g';
  const globalValueRe = new RegExp(valueRe.source, flags);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (contextRe && !contextRe.test(line)) continue;

    globalValueRe.lastIndex = 0;
    let m;
    while ((m = globalValueRe.exec(line)) !== null) {
      const claimed = Number(m[1]);
      if (Number.isFinite(claimed)) {
        claims.push({ line: i + 1, claimed, matchedText: m[0] });
      }
      if (m[0].length === 0) globalValueRe.lastIndex++; // defensive: avoid infinite loop
    }
  }
  return claims;
}

// ---------------------------------------------------------------------------
// Claim registry
// ---------------------------------------------------------------------------

const REGISTRY = [
  {
    id: 'blocked-commands-rules',
    label: 'blocked-commands.json rule count',
    sources: SOURCE_SET_POLICY,
    severity: 'high', // policy/security-relevant — Destructive-Command Guard
    getActual: countBlockedCommandsRules,
    findClaims: (content) => scanLinesForClaim(content, /blocked-commands\.json/, /(\d+)\s+rules?\b/i),
  },
  {
    id: 'rule-files-count',
    label: '.claude/rules/*.md file count',
    sources: SOURCE_SET_POLICY,
    severity: 'medium',
    getActual: countRuleFiles,
    findClaims: (content) => scanLinesForClaim(content, null, /(\d+)\s+rule\s+files?\b/i),
  },
  {
    id: 'skills-count',
    label: 'skills/ user-facing directory count',
    sources: SOURCE_SET_INVENTORY,
    severity: 'medium',
    getActual: countUserFacingSkills,
    findClaims: (content) => scanLinesForClaim(content, null, /(\d+)\s+(?:user-facing\s+)?skills\b/i),
  },
  {
    id: 'commands-count',
    label: 'commands/*.md file count',
    sources: SOURCE_SET_INVENTORY,
    severity: 'medium',
    getActual: countCommands,
    findClaims: (content) => scanLinesForClaim(content, null, /(\d+)\s+(?:slash-)?commands?\b/i),
  },
];

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * @param {string} projectRoot  Absolute path to the consumer project root.
 * @param {object} config       Parsed Session Config (unused — no config gate).
 * @returns {Promise<object>}   { findings, metrics, duration_ms [, skipped_reason] }
 */
// eslint-disable-next-line no-unused-vars -- config kept for probe-contract parity with sibling probes
export async function runProbe(projectRoot, config) {
  const startMs = Date.now();

  const makeSkip = (skipped_reason) => ({
    findings: [],
    metrics: { claims_checked: 0, mismatches: 0, docs_scanned: 0 },
    duration_ms: Date.now() - startMs,
    skipped_reason,
  });

  try {
    // ── Early exit: activation marker absent ──────────────────────────────
    const hasClaudeMd = existsSync(join(projectRoot, 'CLAUDE.md'));
    const hasReadme = existsSync(join(projectRoot, 'README.md'));
    if (!hasClaudeMd && !hasReadme) {
      return makeSkip('CLAUDE.md and README.md not found');
    }

    const findings = [];
    let claimsChecked = 0;
    let mismatches = 0;
    const scannedFiles = new Set();

    for (const entry of REGISTRY) {
      let actual;
      try {
        actual = entry.getActual(projectRoot);
      } catch {
        actual = null;
      }
      // Graceful skip: the underlying code/FS source is missing or
      // unreadable — do not scan or flag claims for this registry entry.
      if (actual === null || actual === undefined) continue;

      for (const relSource of entry.sources) {
        const absSource = join(projectRoot, relSource);
        if (!existsSync(absSource)) continue;

        let content;
        try {
          content = readFileSync(absSource, 'utf8');
        } catch {
          continue;
        }
        scannedFiles.add(relSource);

        const claims = entry.findClaims(content);
        for (const claim of claims) {
          claimsChecked++;
          if (claim.claimed !== actual) {
            mismatches++;
            findings.push({
              severity: entry.severity,
              confidence: 0.9,
              title: `[ssot-code-diff] ${relSource}:${claim.line}: claims ${claim.claimed} but actual is ${actual} (${entry.label})`,
              evidence: {
                claimed: claim.claimed,
                actual,
                file: relSource,
                line: claim.line,
                registry_id: entry.id,
              },
            });
          }
        }
      }
    }

    const durationMs = Date.now() - startMs;
    const metrics = { claims_checked: claimsChecked, mismatches, docs_scanned: scannedFiles.size };

    // ── JSONL append ──────────────────────────────────────────────────────
    try {
      const metricsDir = join(projectRoot, '.orchestrator', 'metrics');
      if (!existsSync(metricsDir)) mkdirSync(metricsDir, { recursive: true });
      const record = {
        timestamp: new Date().toISOString(),
        probe: 'ssot-code-diff',
        project_root: projectRoot,
        claims_checked: claimsChecked,
        mismatches,
        docs_scanned: scannedFiles.size,
        duration_ms: durationMs,
        findings: findings.map((f) => ({
          file: f.evidence.file,
          line: f.evidence.line,
          severity: f.severity,
          claimed: f.evidence.claimed,
          actual: f.evidence.actual,
          registry_id: f.evidence.registry_id,
        })),
      };
      appendFileSync(join(metricsDir, 'ssot-code-diff.jsonl'), JSON.stringify(record) + '\n', 'utf8');
    } catch {
      // JSONL write failure is non-fatal — probe result is still returned
    }

    return { findings, metrics, duration_ms: durationMs };
  } catch (err) {
    // Top-level safety net — probe must never throw
    return {
      findings: [],
      metrics: { claims_checked: 0, mismatches: 0, docs_scanned: 0 },
      duration_ms: Date.now() - startMs,
      skipped_reason: `probe error: ${err.message || err}`,
    };
  }
}

export default runProbe;
