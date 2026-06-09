/**
 * skills/discovery/probes/supply-chain-slopcheck.mjs
 *
 * Discovery probe: supply-chain-slopcheck (#520)
 *
 * Scans package manifests in the repo and classifies each dependency using
 * classifyPackages() from scripts/lib/slopcheck.mjs (Agent A). Reports SLOP,
 * SUS, and ASSUMED packages as findings; LEGITIMATE packages generate no finding.
 *
 * Supported manifest formats:
 *   - package.json         (npm — dependencies + devDependencies)
 *   - requirements.txt     (pip)
 *   - Cargo.toml           (cargo — [dependencies] + [dev-dependencies])
 *
 * Fail-soft contract:
 *   - Missing manifest  → silently skipped
 *   - classifyPackages unavailable (Agent A not yet committed) → skipped finding with summary note
 *   - classifyPackages throws → skipped, error surfaced in summary
 *   - Repo with >500 packages → sample first 100, warn in summary
 *
 * Output shape:
 * {
 *   probe: 'supply-chain-slopcheck',
 *   findings: Finding[],
 *   summary: { total, legitimate, assumed, sus, slop, sampled, errors },
 * }
 *
 * Where Finding = {
 *   severity: 'critical'|'high'|'medium'|'low',
 *   title: string,
 *   evidence: { name, registry, classification, file },
 *   recommendation: string,
 * }
 */

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Maximum packages to classify before sampling. Protects against timeouts. */
const MAX_PACKAGES = 100;

/** Severity mapping per slopcheck classification. */
const SEVERITY_MAP = {
  SLOP: 'critical',
  SUS: 'high',
  ASSUMED: 'medium',
  LEGITIMATE: null, // no finding emitted
};

// ---------------------------------------------------------------------------
// Package extraction helpers
// ---------------------------------------------------------------------------

/**
 * Extract package names from package.json (npm).
 * Reads top-level `dependencies` and `devDependencies`.
 *
 * @param {string} filePath — absolute path to package.json
 * @returns {Array<{name: string, registry: string, file: string}>}
 */
function extractNpmPackages(filePath) {
  let raw;
  try {
    raw = readFileSync(filePath, 'utf8');
  } catch {
    return [];
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [];
  }

  const deps = {
    ...((parsed && typeof parsed.dependencies === 'object' && parsed.dependencies) || {}),
    ...((parsed && typeof parsed.devDependencies === 'object' && parsed.devDependencies) || {}),
  };

  return Object.keys(deps).map((name) => ({
    name,
    registry: 'npm',
    file: filePath,
  }));
}

/**
 * Extract package names from requirements.txt (pip).
 * Handles `pkg>=version`, `pkg==version`, `pkg`, `pkg~=version`.
 * Skips comments, blank lines, VCS/path requirements.
 *
 * @param {string} filePath — absolute path to requirements.txt
 * @returns {Array<{name: string, registry: string, file: string}>}
 */
function extractPipPackages(filePath) {
  let raw;
  try {
    raw = readFileSync(filePath, 'utf8');
  } catch {
    return [];
  }

  const results = [];
  for (const rawLine of raw.split('\n')) {
    const line = rawLine.trim();

    // Skip blank lines, comments, and special markers
    if (!line || line.startsWith('#') || line.startsWith('-') || line.startsWith('.')) continue;
    // Skip VCS requirements (git+, svn+, hg+, bzr+)
    if (/^(git\+|svn\+|hg\+|bzr\+|https?:\/\/)/i.test(line)) continue;

    // Strip inline comments
    const noComment = line.split('#')[0].trim();
    if (!noComment) continue;

    // Extract package name — everything before the first version specifier or bracket
    const nameMatch = noComment.match(/^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)/);
    if (!nameMatch) continue;

    const name = nameMatch[1];
    if (name) {
      results.push({ name, registry: 'pip', file: filePath });
    }
  }

  return results;
}

/**
 * Extract package names from Cargo.toml (cargo).
 * Reads [dependencies] and [dev-dependencies] sections.
 * Skips path deps (`path = "..."`) and git deps (`git = "..."`).
 *
 * @param {string} filePath — absolute path to Cargo.toml
 * @returns {Array<{name: string, registry: string, file: string}>}
 */
function extractCargoPackages(filePath) {
  let raw;
  try {
    raw = readFileSync(filePath, 'utf8');
  } catch {
    return [];
  }

  const results = [];
  let inDepsSection = false;

  for (const rawLine of raw.split('\n')) {
    const line = rawLine.trim();

    // Detect section headers
    if (line.startsWith('[')) {
      // Check if this is a deps section (could be [dependencies], [dev-dependencies],
      // or workspace variants like [workspace.dependencies])
      inDepsSection = /^\[(workspace\.)?dev-dependencies\]$|^\[(workspace\.)?dependencies\]$/.test(line);
      continue;
    }

    if (!inDepsSection) continue;
    // Skip blank lines and comments
    if (!line || line.startsWith('#')) continue;

    // A dep line: name = "version"  or  name = { version = "...", ... }
    const nameMatch = line.match(/^([a-zA-Z0-9_-]+)\s*=/);
    if (!nameMatch) continue;

    const name = nameMatch[1];

    // Skip path and git deps — these are local/VCS, not registry
    if (/\bpath\s*=/.test(line) || /\bgit\s*=/.test(line)) continue;

    results.push({ name, registry: 'cargo', file: filePath });
  }

  return results;
}

// ---------------------------------------------------------------------------
// Slopcheck loader (defensive import — Agent A may not be committed yet)
// ---------------------------------------------------------------------------

/**
 * Attempt to dynamically import classifyPackages from slopcheck.mjs.
 * Returns null if the module is unavailable (Agent A not yet committed).
 *
 * @param {string} repoRoot
 * @returns {Promise<Function|null>}
 */
async function loadClassifyPackages(repoRoot) {
  const slopcheckPath = join(repoRoot, 'scripts', 'lib', 'slopcheck.mjs');
  if (!existsSync(slopcheckPath)) return null;

  try {
    const mod = await import(slopcheckPath);
    if (typeof mod.classifyPackages !== 'function') {
      return null;
    }
    return mod.classifyPackages;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// Finding builder
// ---------------------------------------------------------------------------

/**
 * Build a discovery finding from a classified package result.
 *
 * @param {{ name: string, registry: string, classification: string, evidence?: unknown }} result
 * @param {string} file — source manifest file
 * @returns {object|null} finding object, or null for LEGITIMATE packages
 */
function buildFinding(result, file) {
  const severity = SEVERITY_MAP[result.classification];
  if (!severity) return null; // LEGITIMATE → no finding

  const classLabel = result.classification;

  let recommendation;
  if (result.classification === 'SLOP') {
    recommendation =
      'Package not found in registry. Verify the exact package name is spelled correctly. ' +
      'If intentional (private/local package), mark as experimental in the PRD and document the source.';
  } else if (result.classification === 'SUS') {
    recommendation =
      'Package has audit warnings or suspicious signals. Run `npm audit` / `pip-audit` / `cargo audit` ' +
      'and review the package before using in production.';
  } else {
    // ASSUMED
    recommendation =
      'Package is new or has very low download count. Verify it is the intended package and not a ' +
      'typosquat. Consider pinning to an exact version and reviewing the source.';
  }

  return {
    severity,
    title: `Package "${result.name}" (${result.registry}) classified as ${classLabel}`,
    evidence: {
      name: result.name,
      registry: result.registry,
      classification: classLabel,
      evidence: result.evidence ?? null,
      file,
    },
    recommendation,
  };
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * Discovery probe: supply-chain-slopcheck
 *
 * @param {{ repoRoot: string }} opts
 * @returns {Promise<{probe: string, findings: object[], summary: object}>}
 */
export default async function supplyChainSlopcheck({ repoRoot }) {
  const probe = 'supply-chain-slopcheck';

  // ── 1. Collect packages from all supported manifests ─────────────────────

  const allPackages = [];

  const pkgJsonPath = join(repoRoot, 'package.json');
  if (existsSync(pkgJsonPath)) {
    allPackages.push(...extractNpmPackages(pkgJsonPath));
  }

  const reqsTxtPath = join(repoRoot, 'requirements.txt');
  if (existsSync(reqsTxtPath)) {
    allPackages.push(...extractPipPackages(reqsTxtPath));
  }

  const cargoTomlPath = join(repoRoot, 'Cargo.toml');
  if (existsSync(cargoTomlPath)) {
    allPackages.push(...extractCargoPackages(cargoTomlPath));
  }

  // ── 2. Early exit: no manifest files found ────────────────────────────────

  if (allPackages.length === 0) {
    return {
      probe,
      findings: [],
      summary: {
        total: 0,
        legitimate: 0,
        assumed: 0,
        sus: 0,
        slop: 0,
        sampled: false,
        errors: 0,
      },
    };
  }

  // ── 3. Sample if over limit ───────────────────────────────────────────────

  let sampled = false;
  let packagesToCheck = allPackages;

  if (allPackages.length > MAX_PACKAGES) {
    sampled = true;
    packagesToCheck = allPackages.slice(0, MAX_PACKAGES);
    process.stderr.write(
      `[supply-chain-slopcheck] WARN: ${allPackages.length} packages found — ` +
        `classifying first ${MAX_PACKAGES} only.\n`,
    );
  }

  // ── 4. Load classifyPackages (defensive) ──────────────────────────────────

  const classifyPackages = await loadClassifyPackages(repoRoot);

  if (!classifyPackages) {
    return {
      probe,
      findings: [
        {
          severity: 'low',
          title: 'supply-chain-slopcheck: slopcheck.mjs unavailable',
          evidence: {
            name: 'slopcheck',
            registry: 'internal',
            classification: 'SKIPPED',
            evidence: null,
            file: join(repoRoot, 'scripts', 'lib', 'slopcheck.mjs'),
          },
          recommendation:
            'scripts/lib/slopcheck.mjs has not been committed yet. ' +
            'Re-run /discovery after the slopcheck module is available.',
        },
      ],
      summary: {
        total: allPackages.length,
        legitimate: 0,
        assumed: 0,
        sus: 0,
        slop: 0,
        sampled,
        errors: 0,
        skipped_reason: 'slopcheck-unavailable',
      },
    };
  }

  // ── 5. Classify packages ──────────────────────────────────────────────────

  // Build the input array expected by classifyPackages: [{name, registry}]
  const classifyInput = packagesToCheck.map(({ name, registry }) => ({ name, registry }));

  let classificationResults;
  try {
    classificationResults = await classifyPackages(classifyInput);
  } catch (err) {
    const errMsg = err instanceof Error ? err.message : String(err);
    return {
      probe,
      findings: [],
      summary: {
        total: allPackages.length,
        legitimate: 0,
        assumed: 0,
        sus: 0,
        slop: 0,
        sampled,
        errors: 1,
        skipped_reason: `classifyPackages error: ${errMsg}`,
      },
    };
  }

  // ── 6. Build findings ─────────────────────────────────────────────────────

  const findings = [];
  const summary = {
    total: allPackages.length,
    legitimate: 0,
    assumed: 0,
    sus: 0,
    slop: 0,
    sampled,
    errors: 0,
  };

  // Build a lookup from name+registry → source file (for evidence)
  /** @type {Map<string, string>} */
  const fileMap = new Map();
  for (const pkg of packagesToCheck) {
    fileMap.set(`${pkg.name}::${pkg.registry}`, pkg.file);
  }

  for (const result of classificationResults) {
    const classification = result.classification;

    // Count by classification
    if (classification === 'LEGITIMATE') {
      summary.legitimate++;
    } else if (classification === 'ASSUMED') {
      summary.assumed++;
    } else if (classification === 'SUS') {
      summary.sus++;
    } else if (classification === 'SLOP') {
      summary.slop++;
    } else {
      // Unknown classification — treat as error, emit low finding
      summary.errors++;
      findings.push({
        severity: 'low',
        title: `Package "${result.name}" returned unknown classification: "${classification}"`,
        evidence: {
          name: result.name,
          registry: result.registry ?? 'unknown',
          classification,
          evidence: result.evidence ?? null,
          file: fileMap.get(`${result.name}::${result.registry}`) ?? 'unknown',
        },
        recommendation: 'Unexpected classification from slopcheck. Check slopcheck.mjs for schema changes.',
      });
      continue;
    }

    const sourceFile = fileMap.get(`${result.name}::${result.registry}`) ?? 'unknown';
    const finding = buildFinding({ ...result }, sourceFile);
    if (finding) {
      findings.push(finding);
    }
  }

  return { probe, findings, summary };
}
