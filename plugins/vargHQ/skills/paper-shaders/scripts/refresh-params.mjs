#!/usr/bin/env node
// Rebuild assets/paper-shaders.params.json (names, types, ranges and enum values of
// every documented shader param) from a local copy of Paper's llms.txt. Run it when
// you bump the pinned Paper Shaders version; it makes no network calls itself:
//
//   curl -sL https://shaders.paper.design/llms.txt -o /tmp/paper-llms.txt
//   node scripts/refresh-params.mjs /tmp/paper-llms.txt 0.0.82
//
// Only facts are kept (names, types, ranges, enums, color limits), not Paper's prose.
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const [source, version] = process.argv.slice(2);
if (!source || !version) {
  console.error("usage: node scripts/refresh-params.mjs <llms.txt> <paper-shaders version>");
  process.exit(2);
}

// Props of the React components that are not shader params.
const SKIP = new Set(["width", "height", "minPixelRatio", "maxPixelCount", "speed", "frame"]);
const component = (title) => title.replace(/CMYK/g, "Cmyk").replace(/\s+/g, "");

const shaders = {};
for (const section of readFileSync(source, "utf8").split(/\n(?=### )/)) {
  const title = section.match(/^### (.+)/)?.[1]?.trim();
  const url = section.match(/\*\*URL:\*\* (\S+)/)?.[1];
  if (!title || !url) continue;
  const params = {};
  for (const line of section.split("\n")) {
    const m = line.match(/^- \*\*(\w+)\*\* \(([^)]+)\): (.*)$/);
    if (!m || SKIP.has(m[1])) continue;
    const [, name, type, rest] = m;
    const spec = { type };
    const range = rest.match(/\[min: (-?[\d.]+), max: (-?[\d.]+)(?:, step: ([\d.]+))?\]/);
    if (range) {
      spec.min = Number(range[1]);
      spec.max = Number(range[2]);
      if (range[3]) spec.step = Number(range[3]);
    }
    const options = rest.match(/\[((?:"[^"]+"(?:, )?)+)\]\s*$/);
    if (options) spec.enum = [...options[1].matchAll(/"([^"]+)"/g)].map((o) => o[1]);
    if (name === "fit") spec.enum = ["none", ...(spec.enum ?? ["contain", "cover"])];
    const upTo = rest.match(/Up to (\d+)/i);
    if (name === "colors" && upTo) spec.maxCount = Number(upTo[1]);
    params[name] = spec;
  }
  shaders[component(title)] = { page: url, params };
}

// Sizing params are the same for every shader: keep them once, plus any shader that differs.
const SIZING = ["fit", "scale", "rotation", "offsetX", "offsetY", "originX", "originY", "worldWidth", "worldHeight"];
const sizing = Object.fromEntries(SIZING.map((k) => [k, Object.values(shaders).find((s) => s.params[k])?.params[k]]));
for (const shader of Object.values(shaders)) {
  for (const k of SIZING) {
    if (JSON.stringify(shader.params[k]) === JSON.stringify(sizing[k])) delete shader.params[k];
  }
}

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "assets", "paper-shaders.params.json");
writeFileSync(out, JSON.stringify({ paperShaders: version, source: "https://shaders.paper.design/llms.txt", sizing, shaders }, null, 2) + "\n");
console.log(`${Object.keys(shaders).length} shaders → ${out}`);
