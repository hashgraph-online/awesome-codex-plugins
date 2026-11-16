// SPDX-License-Identifier: MIT
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { deflateRawSync } from "node:zlib";

export const LIMITS = Object.freeze({ inputBytes: 4_000_000, documentBytes: 180_000, fragment: 2_000_000, messages: 120, text: 4000, name: 60, clock: 12 });
const fail = (message) => { throw new Error(message); };
const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const fields = (value, allowed) => {
  if (!object(value) || Object.keys(value).some((key) => !allowed.includes(key))) fail("Unsupported conversation field.");
};
const text = (value, maximum, label) => {
  if (typeof value !== "string" || !value.trim() || value.length > maximum || !value.isWellFormed() || /[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(value)) fail(`Invalid ${label}.`);
  return value;
};

/** Refuse duplicate object keys instead of silently accepting a later value. */
export function parseInput(raw) {
  if (typeof raw !== "string" || Buffer.byteLength(raw) > LIMITS.inputBytes) fail("Input exceeds the size limit.");
  let at = 0;
  const space = () => { while (/[\x20\t\r\n]/.test(raw[at] ?? "") && at < raw.length) at++; };
  const string = () => {
    const start = at++;
    for (; at < raw.length; at++) {
      if (raw[at] === "\\") at++;
      else if (raw[at] === '"') { at++; return JSON.parse(raw.slice(start, at)); }
    }
    fail("Invalid JSON.");
  };
  const value = (depth = 0) => {
    if (depth > 8) fail("JSON is nested too deeply.");
    space();
    if (raw[at] === '"') { string(); return; }
    if (raw[at] === "{" || raw[at] === "[") {
      const isObject = raw[at++] === "{";
      const end = isObject ? "}" : "]";
      const seen = new Set();
      space();
      if (raw[at] === end) { at++; return; }
      for (;;) {
        if (isObject) {
          space();
          if (raw[at] !== '"') fail("Invalid JSON.");
          const key = string();
          if (seen.has(key)) fail("Duplicate JSON field.");
          seen.add(key); space();
          if (raw[at++] !== ":") fail("Invalid JSON.");
        }
        value(depth + 1); space();
        const next = raw[at++];
        if (next === end) return;
        if (next !== ",") fail("Invalid JSON.");
      }
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(raw.slice(at));
    if (!token) fail("Invalid JSON.");
    at += token[0].length;
  };
  value(); space();
  if (at !== raw.length) fail("Invalid JSON.");
  return JSON.parse(raw);
}

/** A deliberately small text-only input, written in the editor's compatible share format. */
export function conversation(input) {
  fields(input, ["name", "messages", "dark", "clock"]);
  const name = text(input.name, LIMITS.name, "name");
  const clock = input.clock === undefined ? "9:41" : text(input.clock, LIMITS.clock, "clock");
  if (input.dark !== undefined && typeof input.dark !== "boolean") fail("Invalid dark setting.");
  if (!Array.isArray(input.messages) || input.messages.length < 1 || input.messages.length > LIMITS.messages) fail("Use 1 through 120 messages.");
  const messages = input.messages.map((message, index) => {
    fields(message, ["from", "text"]);
    if (message.from !== "me" && message.from !== "them") fail('A message sender must be "me" or "them".');
    return { id: `m${index + 1}`, from: message.from, text: text(message.text, LIMITS.text, "message text") };
  });
  return { v: 6, dark: input.dark ?? false, name, clock, messages, replies: false };
}

export function encodeLink(input) {
  const bytes = Buffer.from(JSON.stringify(conversation(input)));
  // Leave room for the editor's phone scene around this text-only document.
  if (bytes.length > LIMITS.documentBytes) fail("Conversation exceeds the size limit.");
  const fragment = `1.${deflateRawSync(bytes).toString("base64url")}`;
  if (fragment.length > LIMITS.fragment) fail("Share link exceeds the size limit.");
  return `https://textmock.com/s#${fragment}`;
}

export async function main(args = process.argv.slice(2)) {
  if (args.length === 1 && args[0] === "--help") {
    process.stdout.write("Usage: node textmock-link.mjs [conversation.json|-]\nReads text-only conversation JSON and prints an editable Textmock link.\n");
    return;
  }
  if (args.length > 1 || (args[0]?.startsWith("-") && args[0] !== "-")) fail("Use a JSON file path or - for stdin.");
  if (Number(process.versions.node.split(".")[0]) < 24) fail("Node.js 24 or later is required.");
  const path = args[0];
  if (path && path !== "-" && !(await stat(path)).isFile()) fail("Input must be a regular JSON file.");
  const input = path && path !== "-" ? createReadStream(path) : process.stdin;
  const chunks = [];
  let size = 0;
  for await (const chunk of input) {
    size += chunk.length;
    if (size > LIMITS.inputBytes) fail("Input exceeds the size limit.");
    chunks.push(Buffer.from(chunk));
  }
  const raw = new TextDecoder("utf-8", { fatal: true }).decode(Buffer.concat(chunks));
  process.stdout.write(`${encodeLink(parseInput(raw))}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(() => { process.stderr.write("Textmock link could not be created. Use valid text-only conversation JSON; see --help and https://textmock.com/docs/agents.\n"); process.exitCode = 2; });
}
