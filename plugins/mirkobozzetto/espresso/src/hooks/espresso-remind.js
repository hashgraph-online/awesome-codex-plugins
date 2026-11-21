#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const { POLICY } = require("../core.cjs");
try {
  const data = JSON.parse(fs.readFileSync(0, "utf8"));
  const prompt = String(data.prompt || "").trim();
  if (!/^\/espresso(?: (?:on|off|status))?$/.test(prompt)) process.exit(0);
  const mode = prompt.split(" ")[1] || "on";
  const text = mode === "off"
    ? "Espresso style is off for this conversation. Follow the user's requested level of detail."
    : mode === "status"
      ? "Espresso provides concise, evidence-preserving style and bundled Ponytail. Use /ponytail status for its mode. Model routing preserves explicit choices."
      : POLICY;
  process.stdout.write(JSON.stringify({hookSpecificOutput: {
    hookEventName: "UserPromptSubmit", additionalContext: text,
  }}));
} catch (error) {
  process.stderr.write(`Espresso command: ${error.message}\n`);
  process.exitCode = 1;
}
