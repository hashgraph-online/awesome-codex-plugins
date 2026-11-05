#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");

function run(args = process.argv.slice(2)) {
  const [harness, ...flags] = args;
  if (!["omp", "pi", "codex"].includes(harness) || flags.some(f => f !== "--apply")) {
    throw new Error("Usage: node src/hooks/install.js omp|pi|codex [--apply]. Without --apply, only show planned files.");
  }
  const apply = flags.includes("--apply");
  const root = path.resolve(__dirname, "../..");
  const home = os.homedir();
  const config = harness === "omp" ? process.env.PI_CODING_AGENT_DIR || path.join(home, ".omp/agent")
    : harness === "pi" ? process.env.PI_CODING_AGENT_DIR || path.join(home, ".pi/agent")
    : process.env.CODEX_HOME || path.join(home, ".codex");
  const files = fs.readdirSync(path.join(root, "skills"), {withFileTypes: true})
    .filter(entry => entry.isDirectory())
    .map(entry => [path.join(config, "skills", entry.name, "SKILL.md"),
      fs.readFileSync(path.join(root, "skills", entry.name, "SKILL.md"), "utf8")]);
  if (harness !== "codex") {
    files.push([path.join(config, "extensions/espresso.ts"), `export { default } from ${JSON.stringify(path.join(root, "src/extension.ts"))};\n`]);
  }
  // Preflight all conflicts before any writes. User settings and credentials stay untouched.
  for (const [file, content] of files) {
    if (fs.existsSync(file) && fs.readFileSync(file, "utf8") !== content) throw new Error(`Existing file differs; refusing overwrite: ${file}`);
  }
  if (apply) for (const [file, content] of files) {
    fs.mkdirSync(path.dirname(file), {recursive: true});
    if (!fs.existsSync(file)) fs.writeFileSync(file, content, {flag: "wx", mode: 0o600});
  }
  return JSON.stringify({apply, harness, files: files.map(([file]) => file), restart: apply}, null, 2);
}
if (require.main === module) {
  try { console.log(run()); } catch (error) { console.error(error.message); process.exitCode = 1; }
} else module.exports = {run};
