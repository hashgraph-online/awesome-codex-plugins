// Purpose: v0.11 — `cam connect --apply` writes a platform's own settings (docs/v0.11/plan.md 3.8): a value at a path
// in a JSON file, an item in a JSON list, or a NAME=value line in an env file. A file that does not parse as plain JSON
// (comments, say) is left alone and the command says so. What was written, and what each setting held before, is
// recorded, and `cam disconnect` puts back only what still holds the value written, so changes the user made since
// stay. The files themselves are never copied: settings files and .env files often hold API keys, and a key does not
// leave its file (as with Codex's .env). Only the settings changed are recorded.
// Input: the edits a platform's entry asks for (core/platform.ts). Output: the files, and
// <data dir>/platforms/<platform>/connected.json.

import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { platformDirOf } from "./request-index.ts";

type Json = Record<string, any>;
// json: the value at that path. add: one item in the list at that path. env: a NAME=value line.
export type ConfigEdit = { file: string; json: string[]; value: unknown } | { file: string; add: string[]; value: unknown } | { file: string; env: string; value: string };
type Recorded = ConfigEdit & { before?: unknown; had: boolean };

const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

export function readJson(file: string): Json {
  if (!existsSync(file)) return {};
  const text = readFileSync(file, "utf8").replace(/^﻿/, "");
  if (!text.trim()) return {};
  try {
    const value = JSON.parse(text);
    if (value && typeof value === "object" && !Array.isArray(value)) return value;
  } catch { /* below */ }
  throw new Error(`${file} is not plain JSON (comments?); change it by hand with the printed steps`);
}

export function jsonAt(file: string, path: string[]): unknown {
  try {
    let node: any = readJson(file);
    for (const key of path) node = node?.[key];
    return node;
  } catch {
    return undefined;
  }
}

const ENV_LINE = (name: string) => new RegExp(`^\\s*(?:export\\s+)?${name}\\s*=\\s*(.*?)\\s*$`);
const unquote = (value: string) => value.replace(/^(["'])(.*)\1$/, "$2");

export function envAt(file: string, name: string): string | undefined {
  if (!existsSync(file)) return undefined;
  for (const line of readFileSync(file, "utf8").split(/\r?\n/)) {
    const match = ENV_LINE(name).exec(line);
    if (match) return unquote(match[1]);
  }
  return undefined;
}

const writeWhole = (file: string, text: string) => {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(`${file}.cam-tmp`, text);
  renameSync(`${file}.cam-tmp`, file);
};

const parentOf = (root: Json, path: string[], create: boolean): Json | null => {
  let node = root;
  for (const key of path.slice(0, -1)) {
    if (node[key] === undefined && create) node[key] = {};
    // A list is walked by index (Qwen Code keeps its models in lists); one is never made here.
    if (!node[key] || typeof node[key] !== "object") return null;
    node = node[key];
  }
  return node;
};

// One file's edits, in order; returns what each found before.
function applyTo(file: string, edits: ConfigEdit[]): Recorded[] {
  const recorded: Recorded[] = [];
  if (edits.every((edit) => "env" in edit)) {
    const eol = existsSync(file) && readFileSync(file, "utf8").includes("\r\n") ? "\r\n" : "\n";
    const lines = existsSync(file) ? readFileSync(file, "utf8").split(/\r?\n/) : [];
    for (const edit of edits as Array<Extract<ConfigEdit, { env: string }>>) {
      const at = lines.findIndex((line) => ENV_LINE(edit.env).test(line));
      const before = at < 0 ? undefined : unquote(ENV_LINE(edit.env).exec(lines[at])![1]);
      recorded.push({ ...edit, had: at >= 0, ...(at >= 0 ? { before } : {}) });
      if (at >= 0) lines[at] = `${edit.env}=${edit.value}`;
      else {
        if (lines.length && lines[lines.length - 1] === "") lines.pop();
        lines.push(`${edit.env}=${edit.value}`, "");
      }
    }
    writeWhole(file, lines.join(eol));
    return recorded;
  }
  const root = readJson(file);
  for (const edit of edits) {
    if ("env" in edit) throw new Error(`${file}: env lines and JSON in one file`);
    const path = "json" in edit ? edit.json : edit.add;
    const parent = parentOf(root, path, true);
    if (!parent) throw new Error(`${file}: ${path.join(".")} is not where a setting can go`);
    const key = path[path.length - 1];
    if ("json" in edit) {
      recorded.push({ ...edit, had: key in parent, ...(key in parent ? { before: parent[key] } : {}) });
      parent[key] = edit.value;
    } else {
      const list = parent[key] === undefined ? (parent[key] = []) : parent[key];
      if (!Array.isArray(list)) throw new Error(`${file}: ${path.join(".")} is not a list`);
      const had = list.some((item: unknown) => same(item, edit.value));
      recorded.push({ ...edit, had });
      if (!had) list.push(edit.value);
    }
  }
  writeWhole(file, `${JSON.stringify(root, null, 2)}\n`);
  return recorded;
}

const recordFile = (root: string, platform: string) => join(platformDirOf(root, platform), "connected.json");

export function applyEdits(platform: string, edits: ConfigEdit[], root: string, now = new Date()): string[] {
  const files = [...new Set(edits.map((edit) => edit.file))];
  // Everything is read and checked before the first file is written.
  for (const file of files) if (!edits.some((edit) => edit.file === file && "env" in edit)) readJson(file);
  const recorded: Recorded[] = [];
  for (const file of files) recorded.push(...applyTo(file, edits.filter((edit) => edit.file === file)));
  // A second connect keeps what was there before the first one.
  const earlier = readRecord(platform, root);
  const kept = recorded.map((entry) => {
    const first = earlier.find((old) => old.file === entry.file && same(pathOf(old), pathOf(entry)) && kind(old) === kind(entry));
    return first ? { ...entry, had: first.had, ...(first.had ? { before: first.before } : { before: undefined }) } : entry;
  });
  writeWhole(recordFile(root, platform), `${JSON.stringify({ at: now.toISOString(), edits: kept }, null, 2)}\n`);
  return files;
}

const kind = (edit: ConfigEdit) => ("json" in edit ? "json" : "add" in edit ? "add" : "env");
const pathOf = (edit: ConfigEdit) => ("json" in edit ? edit.json : "add" in edit ? edit.add : [edit.env]);

function readRecord(platform: string, root: string): Recorded[] {
  try { return JSON.parse(readFileSync(recordFile(root, platform), "utf8")).edits ?? []; } catch { return []; }
}

// Puts back what connect changed, where it still holds the value connect wrote. Returns the settings left as the user
// changed them since.
export function undoEdits(platform: string, root: string): { files: string[]; kept: string[] } {
  const recorded = readRecord(platform, root);
  const kept: string[] = [];
  const files = [...new Set(recorded.map((edit) => edit.file))];
  for (const file of files) {
    if (!existsSync(file)) continue;
    const mine = recorded.filter((edit) => edit.file === file);
    if (mine.every((edit) => "env" in edit)) {
      const eol = readFileSync(file, "utf8").includes("\r\n") ? "\r\n" : "\n";
      let lines = readFileSync(file, "utf8").split(/\r?\n/);
      for (const edit of mine as Array<Recorded & { env: string; value: string }>) {
        const at = lines.findIndex((line) => ENV_LINE(edit.env).test(line));
        if (at < 0 || unquote(ENV_LINE(edit.env).exec(lines[at])![1]) !== edit.value) { kept.push(`${file}: ${edit.env}`); continue; }
        if (edit.had) lines[at] = `${edit.env}=${edit.before}`;
        else lines = lines.filter((_, index) => index !== at);
      }
      writeWhole(file, lines.join(eol));
      continue;
    }
    let doc: Json;
    try { doc = readJson(file); } catch { kept.push(file); continue; }
    for (const edit of mine) {
      if ("env" in edit) continue;
      const path = "json" in edit ? edit.json : edit.add;
      const parent = parentOf(doc, path, false);
      const key = path[path.length - 1];
      if (!parent) { kept.push(`${file}: ${path.join(".")}`); continue; }
      if ("json" in edit) {
        if (!same(parent[key], edit.value)) { kept.push(`${file}: ${path.join(".")}`); continue; }
        if (edit.had) parent[key] = edit.before;
        else delete parent[key];
      } else if (Array.isArray(parent[key]) && !edit.had) {
        parent[key] = parent[key].filter((item: unknown) => !same(item, edit.value));
      }
    }
    writeWhole(file, `${JSON.stringify(doc, null, 2)}\n`);
  }
  if (recorded.length) writeWhole(recordFile(root, platform), `${JSON.stringify({ at: new Date().toISOString(), edits: [] }, null, 2)}\n`);
  return { files, kept };
}
