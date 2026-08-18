/**
 * skills/discovery/probes/docs-staleness.mjs
 *
 * Probe: detects stale "living" docs — direct `docs/*.md` files plus
 * `docs/examples/*.md` files whose filesystem mtime is older than the
 * `docs-staleness.thresholds.living` config threshold (default 90 days).
 *
 * Deliberately excludes `docs/adr/` (historically stable, immutable-by-design
 * decision records — staleness is expected and desired) and `docs/prd/`
 * (active work-in-progress documents scoped to a project's lifecycle, not
 * "living reference docs"). Only the two directories named above are
 * scanned; other docs/ subdirectories (audit, research, spikes, ...) are
 * intentionally out of scope for this probe.
 *
 * Unlike the vault-narrative-staleness probe, staleness here is measured via
 * filesystem mtime, not a YAML frontmatter `updated:` field — most repo docs
 * under docs/ carry no frontmatter at all.
 *
 * Severity escalation relative to threshold T (in days):
 *   age_days > T * 3  → high
 *   age_days > T * 2  → medium
 *   age_days > T      → low
 *
 * Thresholds are read from Session Config `docs-staleness.thresholds.living`
 * (fail-soft: non-numeric / non-positive values fall back to the 90-day default).
 *
 * Input: projectRoot (absolute path to the repo running discovery), config
 * (parsed Session Config object, may be empty/partial).
 *
 * Output: {findings[], metrics, duration_ms, [skipped_reason]}. Never throws.
 * Also appends one JSONL summary record to .orchestrator/metrics/docs-staleness.jsonl.
 */

import { existsSync, readdirSync, statSync, mkdirSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEFAULT_THRESHOLD_DAYS = 90;
const DAY_MS = 86_400_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function resolveThreshold(config) {
  const raw = config?.['docs-staleness']?.thresholds?.living;
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return DEFAULT_THRESHOLD_DAYS;
  return n;
}

function computeSeverity(ageDays, threshold) {
  if (ageDays > threshold * 3) return 'high';
  if (ageDays > threshold * 2) return 'medium';
  return 'low';
}

/** List *.md filenames directly inside dirPath (non-recursive). Never throws. */
function listMarkdownFiles(dirPath) {
  if (!existsSync(dirPath)) return [];
  let entries;
  try {
    entries = readdirSync(dirPath, { withFileTypes: true });
  } catch {
    return [];
  }
  return entries.filter((e) => e.isFile() && e.name.endsWith('.md')).map((e) => e.name);
}

function makeMetricsPath(projectRoot) {
  return join(projectRoot, '.orchestrator', 'metrics');
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * @param {string} projectRoot  Absolute path to the consumer project root.
 * @param {object} config       Parsed Session Config (may be empty / partial).
 * @returns {Promise<object>}   { findings, metrics, duration_ms [, skipped_reason] }
 */
export async function runProbe(projectRoot, config) {
  const startMs = Date.now();

  const makeSkip = (skipped_reason) => ({
    findings: [],
    metrics: { scanned_docs: 0, stale_docs: 0, errors: 0 },
    duration_ms: Date.now() - startMs,
    skipped_reason,
  });

  try {
    const docsDir = join(projectRoot, 'docs');

    // ── Early exit: docs/ directory absent ────────────────────────────────
    if (!existsSync(docsDir)) {
      return makeSkip('docs/ directory not found');
    }

    const threshold = resolveThreshold(config);
    const now = Date.now();

    const findings = [];
    let scannedDocs = 0;
    let staleDocs = 0;
    let errors = 0;

    // Root-level docs/*.md + docs/examples/*.md only (see file-header note).
    const targets = [
      ...listMarkdownFiles(docsDir).map((name) => ({ rel: name, abs: join(docsDir, name) })),
      ...listMarkdownFiles(join(docsDir, 'examples')).map((name) => ({
        rel: join('examples', name),
        abs: join(docsDir, 'examples', name),
      })),
    ];

    for (const { rel, abs } of targets) {
      scannedDocs++;

      let mtimeMs;
      try {
        mtimeMs = statSync(abs).mtimeMs;
      } catch (err) {
        errors++;
        findings.push({
          severity: 'low',
          confidence: 0.6,
          title: `[docs-staleness] ${rel}: cannot stat file`,
          evidence: { file: rel, error: err.message || String(err) },
        });
        continue;
      }

      const ageDays = (now - mtimeMs) / DAY_MS;
      if (ageDays > threshold) {
        staleDocs++;
        const ageDaysRounded = Math.round(ageDays);
        const severity = computeSeverity(ageDays, threshold);
        findings.push({
          severity,
          confidence: 0.9,
          title: `[docs-staleness] ${rel}: ${ageDaysRounded}d since last change (threshold: ${threshold}d)`,
          evidence: {
            file: rel,
            age_days: ageDaysRounded,
            threshold_days: threshold,
          },
        });
      }
    }

    const durationMs = Date.now() - startMs;
    const metrics = { scanned_docs: scannedDocs, stale_docs: staleDocs, errors };

    // ── JSONL append ──────────────────────────────────────────────────────
    try {
      const metricsDir = makeMetricsPath(projectRoot);
      if (!existsSync(metricsDir)) mkdirSync(metricsDir, { recursive: true });
      const record = {
        timestamp: new Date().toISOString(),
        probe: 'docs-staleness',
        project_root: projectRoot,
        scanned_docs: scannedDocs,
        stale_docs: staleDocs,
        errors,
        duration_ms: durationMs,
        findings: findings.map((f) => ({
          file: f.evidence.file,
          severity: f.severity,
          age_days: f.evidence.age_days ?? null,
          threshold_days: f.evidence.threshold_days ?? threshold,
        })),
      };
      appendFileSync(join(metricsDir, 'docs-staleness.jsonl'), JSON.stringify(record) + '\n', 'utf8');
    } catch {
      // JSONL write failure is non-fatal — probe result is still returned
    }

    return { findings, metrics, duration_ms: durationMs };
  } catch (err) {
    // Top-level safety net — probe must never throw
    return {
      findings: [],
      metrics: { scanned_docs: 0, stale_docs: 0, errors: 1 },
      duration_ms: Date.now() - startMs,
      skipped_reason: `probe error: ${err.message || err}`,
    };
  }
}

export default runProbe;
