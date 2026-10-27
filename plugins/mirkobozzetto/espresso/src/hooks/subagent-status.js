#!/usr/bin/env node
"use strict";
// One row per running agent: name, model, effort and tokens, so the user sees
// which model and effort each agent actually uses.
const fs = require("node:fs");

try {
  const input = JSON.parse(fs.readFileSync(0, "utf8") || "{}");
  const width = Number(input.columns) || 100;
  for (const task of input.tasks || []) {
    const model = String(task.model || "").replace(/^claude-/, "").replace(/-\d{8}$/, "");
    const tokens = task.tokenCount ? `${Math.round(task.tokenCount / 1000)}k tokens` : "";
    const parts = [task.name || task.type, model, task.effort, tokens, task.description].filter(Boolean);
    let content = parts.join(" · ");
    if (content.length > width) content = `${content.slice(0, width - 1)}…`;
    process.stdout.write(`${JSON.stringify({id: task.id, content})}\n`);
  }
} catch {
  // Printing nothing keeps Claude Code's default rows.
}
