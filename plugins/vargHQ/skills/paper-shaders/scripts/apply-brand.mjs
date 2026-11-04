#!/usr/bin/env node
// Put a brand palette into a preset through its `roles` map. Roles the palette
// does not define keep the preset's color; `accent@0.48` keeps 48% alpha.
// Writes the branded preset to stdout (or --out), and lists unmapped roles on stderr.
//
//   node scripts/apply-brand.mjs assets/presets/brand-mesh.json palette.json > presets/brand-mesh.json
//   node scripts/apply-brand.mjs assets/presets/god-rays-reveal.json palette.json --id acme-rays --out presets/acme-rays.json
//
// palette.json: { "base": "#0b0b0f", "ink": "#ffffff", "accent": "#3b5bfd", "accent-light": "#8ea2ff",
//                 "deep": "#1b1446", "paper": "#f4efe6", "shadow": "#9c8a70", "highlight": "#ffffff" }
import { readFileSync, writeFileSync } from "node:fs";

const args = process.argv.slice(2);
const flag = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const [presetFile, paletteFile] = args.filter((a, i) => !a.startsWith("--") && !["--id", "--out"].includes(args[i - 1]));
if (!presetFile || !paletteFile) {
  console.error("usage: node scripts/apply-brand.mjs <preset.json> <palette.json> [--id new-id] [--out file]");
  process.exit(2);
}

const preset = JSON.parse(readFileSync(presetFile, "utf8"));
const palette = JSON.parse(readFileSync(paletteFile, "utf8"));
const unmapped = new Set();

const color = (spec, fallback) => {
  const [role, alpha] = String(spec).split("@");
  const hex = normalize(palette[role]);
  if (!hex) {
    unmapped.add(role);
    return fallback;
  }
  return alpha === undefined ? hex : hex + Math.round(Number(alpha) * 255).toString(16).padStart(2, "0");
};

for (const [param, role] of Object.entries(preset.roles ?? {})) {
  const current = preset.params[param];
  preset.params[param] = Array.isArray(role) ? role.map((r, i) => color(r, current?.[i])) : color(role, current);
}
const id = flag("--id");
if (id) preset.id = id;

const json = JSON.stringify(preset, null, 2) + "\n";
const out = flag("--out");
if (out) writeFileSync(out, json);
else process.stdout.write(json);
if (unmapped.size) console.error(`kept the preset's colors for roles not in the palette: ${[...unmapped].join(", ")}`);

function normalize(value) {
  if (typeof value !== "string") return undefined;
  const short = value.match(/^#([0-9a-f])([0-9a-f])([0-9a-f])$/i);
  if (short) return `#${short[1]}${short[1]}${short[2]}${short[2]}${short[3]}${short[3]}`.toLowerCase();
  if (/^#[0-9a-f]{6}$/i.test(value)) return value.toLowerCase();
  console.error(`palette colors must be #rgb or #rrggbb, got "${value}"`);
  process.exit(1);
}
