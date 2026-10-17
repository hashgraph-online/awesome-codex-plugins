#!/usr/bin/env node
// Fail-open on any error: a broken hook must never block a read.
// Do not reference unset ${VAR} from hooks.json; grok refuses to spawn those.

import { spawnSync } from "node:child_process";
import { writeSync } from "node:fs";
import { extname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const COMPRESSIBLE = new Set([".md", ".markdown", ".html", ".htm", ".txt"]);

const INPUT_KEYS = ["tool_input", "toolInput", "input", "arguments", "params"];
const PATH_KEYS = [
  "file_path", "filePath", "FilePath",
  "target_file", "targetFile", "TargetFile",
  "absolute_path", "absolutePath", "AbsolutePath",
  "path", "Path",
];

function readStdin() {
  return new Promise((done) => {
    let data = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => { data += chunk; });
    process.stdin.on("end", () => done(data));
    // Some hosts may keep stdin open longer than the payload needs.
    setTimeout(() => done(data), 5000).unref();
  });
}

function firstString(obj, keys) {
  for (const key of keys) {
    const value = obj[key];
    if (typeof value === "string" && value.length > 0) return value;
  }
  return "";
}

function toolArgs(data) {
  for (const key of INPUT_KEYS) {
    const value = data[key];
    if (typeof value === "object" && value !== null) return value;
  }
  const call = data.toolCall || data.tool_call;
  if (typeof call === "object" && call !== null) {
    const args = call.args || call.arguments || call.input;
    if (typeof args === "object" && args !== null) return args;
  }
  return data;
}

export function extractFilePath(payload) {
  try {
    const data = JSON.parse(payload);
    if (typeof data !== "object" || data === null) return "";
    return firstString(toolArgs(data), PATH_KEYS);
  } catch {
    return "";
  }
}

export function denyOutput(transpiled, payload) {
  try {
    const data = JSON.parse(payload);
    if (data && typeof data === "object" && (data.toolCall || data.tool_call)) {
      return { decision: "deny", reason: transpiled };
    }
  } catch {
    // fall through to the Claude/Codex/grok envelope
  }
  return {
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: transpiled,
    },
  };
}

function isMainModule() {
  const entry = process.argv[1];
  if (!entry) return false;
  try {
    return fileURLToPath(import.meta.url) === resolve(entry);
  } catch {
    return false;
  }
}

if (isMainModule()) {
  const payload = await readStdin();
  const filePath = extractFilePath(payload);
  if (!filePath || !COMPRESSIBLE.has(extname(filePath).toLowerCase())) {
    process.exit(0);
  }

  const result = spawnSync(
    "transpile",
    ["--input", filePath, "--fidelity", "semantic", "--quiet"],
    { stdio: ["ignore", "pipe", "pipe"], maxBuffer: 64 * 1024 * 1024 },
  );
  const transpiled = result.status === 0 && result.stdout
    ? result.stdout.toString("utf8").trim()
    : "";
  if (!transpiled) process.exit(0);

  writeSync(1, JSON.stringify(denyOutput(transpiled, payload)));
}
