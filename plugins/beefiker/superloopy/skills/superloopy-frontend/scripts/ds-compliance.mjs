#!/usr/bin/env node
// Dependency-free Design System Compliance gate for the Superloopy frontend skill.
// Turns "is the UI on-system?" into a measurable pass/fail: it flags raw hex colors
// not declared in DESIGN.md and off-scale spacing (px not on the base unit) — the
// "Lighthouse 100 but 14 undeclared hex codes" failure that reads as AI slop.
//
// Exits non-zero when violations exist, so it drops straight into the loop:
//   superloopy loop prove -- node skills/superloopy-frontend/scripts/ds-compliance.mjs DESIGN.md src/**/*.css
// Uses only node:fs. Exports parse/scan for tests.

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const HEX = /#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g;
const SPACING_PROP = /\b(padding|margin|gap|inset|top|right|bottom|left|row-gap|column-gap)\b[^:;{}]*:\s*([^;{}]+)/gi;
const PX = /\b(\d+)px\b/g;
// 0 and 1px (hairline borders/insets) are always allowed; do not flag them as magic.
const ALLOWED_PX = new Set([0, 1]);

function normalizeHex(hex) {
  let h = hex.replace("#", "").toLowerCase();
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  return `#${h}`;
}

// Parse DESIGN.md into { colors:Set<normalizedHex>, base:number }.
export function parseDesignTokens(designText) {
  const colors = new Set();
  for (const m of designText.matchAll(HEX)) colors.add(normalizeHex(m[0]));
  const baseMatch = designText.match(/base[^\n]*?\b(\d+)\s*px/i);
  const base = baseMatch ? Number.parseInt(baseMatch[1], 10) : 4;
  return { colors, base: base > 0 ? base : 4 };
}

// Scan one file's content against tokens. Returns violation objects with 1-indexed lines.
export function scanContent(content, tokens, file = "<content>") {
  const lines = content.split("\n");
  const violations = [];
  lines.forEach((line, i) => {
    for (const m of line.matchAll(HEX)) {
      const norm = normalizeHex(m[0]);
      if (!tokens.colors.has(norm)) {
        violations.push({ file, line: i + 1, kind: "undeclared-color", value: m[0], snippet: line.trim().slice(0, 120) });
      }
    }
    for (const decl of line.matchAll(SPACING_PROP)) {
      for (const px of decl[2].matchAll(PX)) {
        const n = Number.parseInt(px[1], 10);
        if (!ALLOWED_PX.has(n) && n % tokens.base !== 0) {
          violations.push({ file, line: i + 1, kind: "off-scale-spacing", value: `${n}px`, snippet: line.trim().slice(0, 120) });
        }
      }
    }
  });
  return violations;
}

export function checkFiles(designPath, targetPaths) {
  const tokens = parseDesignTokens(readFileSync(designPath, "utf8"));
  const violations = [];
  for (const path of targetPaths) {
    violations.push(...scanContent(readFileSync(path, "utf8"), tokens, path));
  }
  const byKind = violations.reduce((acc, v) => ({ ...acc, [v.kind]: (acc[v.kind] ?? 0) + 1 }), {});
  return {
    ok: violations.length === 0,
    design: designPath,
    base: tokens.base,
    declaredColors: tokens.colors.size,
    counts: byKind,
    violations
  };
}

function main(argv) {
  const [design, ...targets] = argv;
  if (!design || targets.length === 0) {
    process.stderr.write("usage: ds-compliance.mjs <DESIGN.md> <file...>\n");
    process.exit(2);
  }
  const result = checkFiles(design, targets);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  process.exit(result.ok ? 0 : 1);
}

// pathToFileURL (not `file://${argv[1]}`): on Windows argv[1] is `C:\...` while
// import.meta.url is `file:///C:/...`, so the string compare never matched and the
// gate silently exited 0 — a passing evidence artifact for an unchecked UI.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main(process.argv.slice(2));
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(2);
  }
}
