#!/usr/bin/env node
// Scaffold a HyperFrames project that uses Paper Shaders, or add the runtime files
// to an existing one. Copies paper-preset.js and the presets; writes nothing else
// into an existing project.
//
//   node scripts/new-project.mjs ./my-video                          # shader-background template
//   node scripts/new-project.mjs ./reel --example preset-reel        # the nine-preset reel
//   node scripts/new-project.mjs ./gallery --example paper-gallery   # Paper's 124 built-in presets
//   node scripts/new-project.mjs ./existing-project --add            # paper-preset.js + presets/ only
import { cpSync, existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HYPERFRAMES_VERSION = "0.8.206";
const skill = join(dirname(fileURLToPath(import.meta.url)), "..");
const COMPOSITIONS = {
  "shader-background": join(skill, "templates", "hyperframes", "shader-background.html"),
  "preset-reel": join(skill, "examples", "preset-reel", "index.html"),
  "paper-gallery": join(skill, "examples", "paper-gallery", "index.html"),
};

const args = process.argv.slice(2);
const dir = args.find((a) => !a.startsWith("--") && args[args.indexOf(a) - 1] !== "--example");
const example = args.includes("--example") ? args[args.indexOf("--example") + 1] : "shader-background";
const add = args.includes("--add");
const force = args.includes("--force");
if (!dir || !COMPOSITIONS[example]) {
  console.error(`usage: node scripts/new-project.mjs <dir> [--example ${Object.keys(COMPOSITIONS).join("|")}] [--add] [--force]`);
  process.exit(2);
}

const target = resolve(dir);
if (add) {
  if (!existsSync(join(target, "index.html"))) fail(`${target} has no index.html; is it a HyperFrames project?`);
} else if (existsSync(target) && readdirSync(target).length > 0) {
  fail(`${target} is not empty; use --add to add the runtime files to an existing project`);
}
mkdirSync(join(target, "presets", "paper"), { recursive: true });

const copy = (from, to) => {
  if (existsSync(to) && !force) fail(`${to} exists; pass --force to overwrite`);
  cpSync(from, to);
  if (!to.includes("/presets/paper/")) console.log(`  ${to.replace(`${target}/`, "")}`);
};

console.log(`${add ? "Adding to" : "Creating"} ${target} (plus Paper's built-in presets in presets/paper/)`);
copy(join(skill, "templates", "paper-preset.js"), join(target, "paper-preset.js"));
// presets/*.json are the varg presets; presets/paper/*.json are Paper's own, as on shaders.paper.design.
for (const f of readdirSync(join(skill, "assets", "presets"), { recursive: true }).filter((f) => f.endsWith(".json"))) {
  copy(join(skill, "assets", "presets", f), join(target, "presets", f));
}

if (!add) {
  copy(COMPOSITIONS[example], join(target, "index.html"));
  const npx = `npx --yes hyperframes@${HYPERFRAMES_VERSION}`;
  writeFileSync(
    join(target, "package.json"),
    JSON.stringify(
      {
        name: basename(target),
        private: true,
        type: "module",
        scripts: { dev: `${npx} preview`, check: `${npx} check`, render: `${npx} render` },
      },
      null,
      2,
    ) + "\n",
  );
  writeFileSync(
    join(target, "hyperframes.json"),
    JSON.stringify(
      {
        $schema: "https://hyperframes.heygen.com/schema/hyperframes.json",
        registry: "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
        paths: { blocks: "compositions", components: "compositions/components", assets: "assets" },
        media: { autoProxy: true },
      },
      null,
      2,
    ) + "\n",
  );
  console.log("  package.json\n  hyperframes.json");
}

console.log(`\nNext (pinned to hyperframes@${HYPERFRAMES_VERSION}): cd ${dir} && npm run check && npx --yes hyperframes@${HYPERFRAMES_VERSION} snapshot --at 1,2 && npm run render -- --output out.mp4`);

function fail(message) {
  console.error(message);
  process.exit(1);
}
