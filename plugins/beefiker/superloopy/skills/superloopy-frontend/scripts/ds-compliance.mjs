#!/usr/bin/env node
// Compatibility filename for the dependency-free partial color/spacing token lint.
// It flags raw hex colors not declared in DESIGN.md and off-scale spacing (px not
// on the base unit); it makes no broader typography, component, or accessibility claim.
//
// Exits non-zero when violations exist, so it drops straight into the loop:
//   superloopy loop prove -- node skills/superloopy-frontend/scripts/ds-compliance.mjs DESIGN.md src/**/*.css
// Uses only node:fs. Exports parse/scan for tests.

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const HEX = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-fA-F])/g;
const BOX_AXIS = "(?:top|right|bottom|left|block(?:-start|-end)?|inline(?:-start|-end)?)";
const SPACING_NAME = `(?:(?:padding|margin|scroll-padding|scroll-margin)(?:-${BOX_AXIS})?|gap|row-gap|column-gap|grid-gap|grid-row-gap|grid-column-gap|inset(?:-(?:block(?:-start|-end)?|inline(?:-start|-end)?))?|top|right|bottom|left)`;
const SPACING_DECL = new RegExp(`(?:^|[;{])\\s*(${SPACING_NAME})\\s*:\\s*([^;{}]+)(?=;|\\})`, "gimu");
const PX = /(?<![\w.])(-?(?:\d*\.\d+|\d+))px\b/g;
// 0 and 1px (hairline borders/insets) are always allowed; do not flag them as magic.
const ALLOWED_PX = new Set([0, 1]);

function normalizeHex(hex) {
  let h = hex.replace("#", "").toLowerCase();
  if (h.length === 3 || h.length === 4) h = h.split("").map((c) => c + c).join("");
  return `#${h}`;
}

// Parse DESIGN.md into { colors:Set<normalizedHex>, base:number }.
export function parseDesignTokens(designText) {
  const colors = new Set();
  for (const m of designText.matchAll(HEX)) colors.add(normalizeHex(m[0]));
  const baseMatch = designText.match(/\bbase\b[^\n]*?\b(\d+)\s*px/i);
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
  });

  for (const decl of content.matchAll(SPACING_DECL)) {
    const valueOffset = decl[0].lastIndexOf(decl[2]);
    const valueStart = decl.index + valueOffset;
    for (const px of decl[2].matchAll(PX)) {
      const n = Number.parseFloat(px[1]);
      const magnitude = Math.abs(n);
      if (!ALLOWED_PX.has(magnitude) && magnitude % tokens.base !== 0) {
        const line = content.slice(0, valueStart + px.index).split("\n").length;
        violations.push({
          file,
          line,
          kind: "off-scale-spacing",
          value: `${px[1]}px`,
          snippet: lines[line - 1].trim().slice(0, 120),
        });
      }
    }
  }
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
