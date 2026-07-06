/**
 * skills/discovery/probes/frontend-slop.mjs
 *
 * Discovery probe: frontend-slop
 *
 * Walks the repo for frontend source files (CSS/HTML/JSX/TSX/Vue/Svelte/Astro)
 * and runs the deterministic frontend-slop detector (scripts/lib/frontend-detect)
 * over them. Reports AI-generated design tells + quality issues as findings.
 *
 * Zero LLM, zero network, zero browser — pure regex tier. Inspired by
 * pbakaus/impeccable's detector (Apache-2.0); clean-room reimplementation that
 * deliberately omits impeccable's heavier static-HTML + Puppeteer tiers.
 *
 * Fail-soft contract:
 *   - No frontend files          → empty findings, total 0
 *   - Unreadable file            → skipped silently
 *   - >MAX_FILES scannable files → sample first MAX_FILES, warn in summary
 *   - detector module missing    → single low finding (defensive, like
 *                                  supply-chain-slopcheck)
 *
 * Output shape:
 * {
 *   probe: 'frontend-slop',
 *   findings: Finding[],
 *   summary: { total, high, medium, low, aiSlop, quality, filesScanned, sampled, errors }
 * }
 */

import { existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

/** Max files to scan before sampling — protects against huge trees. */
const MAX_FILES = 2000;

/** Directories never worth walking. */
const SKIP_DIRS = new Set([
  'node_modules',
  '.git',
  'dist',
  'build',
  'out',
  '.next',
  '.nuxt',
  '.svelte-kit',
  '.astro',
  'coverage',
  '.cache',
  'vendor',
  '.orchestrator',
]);

/**
 * Map a detector finding to the discovery-probe finding shape.
 * @param {import('../../../scripts/lib/frontend-detect/detect.mjs').Finding} f
 * @param {string} repoRoot
 */
function toProbeFinding(f, repoRoot) {
  const relFile = f.file.startsWith(repoRoot) ? f.file.slice(repoRoot.length + 1) : f.file;
  return {
    severity: f.severity, // high|medium|low — already in the probe vocabulary
    title: `${f.title} — ${relFile}:${f.line}`,
    evidence: {
      rule: f.rule,
      ruleRef: f.ruleRef,
      category: f.category,
      file: relFile,
      line: f.line,
      snippet: f.snippet,
      fpRisk: f.fpRisk,
    },
    recommendation: f.recommendation,
  };
}

/**
 * Bounded recursive walk collecting scannable frontend files.
 * @param {string} dir
 * @param {Set<string>} exts
 * @param {string[]} acc
 * @returns {boolean} true if the MAX_FILES cap was hit (sampled)
 */
function walk(dir, exts, acc) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return false;
  }
  for (const entry of entries) {
    if (acc.length >= MAX_FILES) return true;
    if (entry.name.startsWith('.') && entry.isDirectory() && !SKIP_DIRS.has(entry.name)) {
      // Skip hidden dirs except when explicitly walkable; cheaper to skip all dotdirs.
      continue;
    }
    const full = join(dir, entry.name);
    let isDir = entry.isDirectory();
    let isFile = entry.isFile();
    if (!isDir && !isFile) {
      // Some filesystems need an explicit stat (e.g. symlinks).
      try {
        const st = statSync(full);
        isDir = st.isDirectory();
        isFile = st.isFile();
      } catch {
        continue;
      }
    }
    if (isDir) {
      if (SKIP_DIRS.has(entry.name)) continue;
      if (walk(full, exts, acc)) return true;
    } else if (isFile) {
      const dot = entry.name.lastIndexOf('.');
      const ext = dot === -1 ? '' : entry.name.slice(dot).toLowerCase();
      if (exts.has(ext)) acc.push(full);
    }
  }
  return false;
}

/**
 * Discovery probe entry point.
 * @param {{ repoRoot: string }} opts
 * @returns {Promise<{probe: string, findings: object[], summary: object}>}
 */
export default async function frontendSlop({ repoRoot }) {
  const probe = 'frontend-slop';

  // Defensive import — mirrors supply-chain-slopcheck's pattern so the probe
  // never hard-crashes the discovery run if the detector is absent.
  const detectPath = join(repoRoot, 'scripts', 'lib', 'frontend-detect', 'detect.mjs');
  if (!existsSync(detectPath)) {
    return {
      probe,
      findings: [
        {
          severity: 'low',
          title: 'frontend-slop: detector module unavailable',
          evidence: { file: detectPath, classification: 'SKIPPED' },
          recommendation:
            'scripts/lib/frontend-detect/detect.mjs is missing. Re-run /discovery after it is committed.',
        },
      ],
      summary: { total: 0, filesScanned: 0, sampled: false, errors: 0, skipped_reason: 'detector-unavailable' },
    };
  }

  let detectFiles, SCANNABLE_EXTS;
  try {
    ({ detectFiles, SCANNABLE_EXTS } = await import(detectPath));
  } catch (err) {
    return {
      probe,
      findings: [],
      summary: {
        total: 0,
        filesScanned: 0,
        sampled: false,
        errors: 1,
        skipped_reason: `detector import failed: ${err instanceof Error ? err.message : String(err)}`,
      },
    };
  }

  const files = [];
  const sampled = walk(repoRoot, SCANNABLE_EXTS, files);
  if (sampled) {
    process.stderr.write(`[frontend-slop] WARN: file cap (${MAX_FILES}) hit — scanning a sample.\n`);
  }

  const raw = detectFiles(files);
  const findings = raw.map((f) => toProbeFinding(f, repoRoot));

  const summary = {
    total: findings.length,
    high: raw.filter((f) => f.severity === 'high').length,
    medium: raw.filter((f) => f.severity === 'medium').length,
    low: raw.filter((f) => f.severity === 'low').length,
    aiSlop: raw.filter((f) => f.category === 'ai-slop').length,
    quality: raw.filter((f) => f.category === 'quality').length,
    filesScanned: files.length,
    sampled,
    errors: 0,
  };

  return { probe, findings, summary };
}
