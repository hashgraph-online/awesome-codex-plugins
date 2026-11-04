#!/usr/bin/env node
// Regenerate assets/refs.manifest.json: every preset (role "shader") with its hash,
// size and license, plus the link refs the skill points people to. Run it after
// changing a preset; validate-presets.mjs should pass first.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const presetsDir = join(root, "assets", "presets");

const presets = readdirSync(presetsDir, { recursive: true })
  .filter((f) => f.endsWith(".json"))
  .sort()
  .map((file) => {
    const bytes = readFileSync(join(presetsDir, file));
    const preset = JSON.parse(bytes.toString("utf8"));
    return {
      id: preset.id,
      role: "shader",
      path: `assets/presets/${file}`,
      url: preset.page,
      sha256: createHash("sha256").update(bytes).digest("hex"),
      bytes: bytes.length,
      license: "Apache-2.0",
      controls: preset.use,
      must_not_touch: preset.image ? "the shape of the logo or still it is given" : "text and logos layered over it",
    };
  });

const links = [
  {
    id: "paper-shaders-llms",
    role: "link",
    url: "https://shaders.paper.design/llms.txt",
    license: "link-only",
    controls: "every documented shader prop and its range, for writing new presets",
  },
  {
    id: "paper-shaders-license",
    role: "link",
    url: "https://github.com/paper-design/shaders/blob/main/LICENSE",
    license: "link-only",
    controls: "the Apache-2.0 terms the presets and templates rely on",
  },
  {
    id: "hyperframes-frame-sources",
    role: "link",
    url: "https://hyperframes.heygen.com/guides/frame-sources.md",
    license: "link-only",
    controls: "how HyperFrames drives scene code from its timeline",
  },
];

writeFileSync(join(root, "assets", "refs.manifest.json"), JSON.stringify([...presets, ...links], null, 2) + "\n");
console.log(`${presets.length} presets and ${links.length} links → assets/refs.manifest.json`);
