#!/usr/bin/env node
// llm-transpile PreToolUse hook
// Fires before Read — compresses .md/.html/.txt and blocks the original Read.

"use strict";

const { spawnSync } = require("child_process");
const { extname } = require("path");

const COMPRESSIBLE = new Set([".md", ".markdown", ".html", ".htm", ".txt"]);

let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", () => {
  try {
    const data = JSON.parse(input);
    const filePath = (data.tool_input || data.input || {}).file_path || "";
    const ext = extname(filePath).toLowerCase();

    // Only compress whitelisted extensions
    if (!COMPRESSIBLE.has(ext)) {
      process.exit(0);
    }

    // Run transpile — binary auto-detects format from extension
    const result = spawnSync("transpile", [
      "--input", filePath,
      "--fidelity", "semantic",
      "--quiet",
    ], { stdio: ["pipe", "pipe", "pipe"] });

    if (!result.error && result.status === 0 && result.stdout.length > 0) {
      process.stdout.write(result.stdout);
      process.exit(2); // Block original Read; agent sees transpiled output
    }
  } catch (_) {}

  // Any failure: let Read proceed normally
  process.exit(0);
});
