#!/usr/bin/env node

/**
 * upload-asset.mjs - Upload a local image file to Shots and attach it to an app.
 *
 * Usage:
 *   node upload-asset.mjs --file ./icon.png --app-id <appId> --kind icon
 *   node upload-asset.mjs --file ./ref.png --app-id <appId> --kind reference --locale en-US
 *
 * Options:
 *   --file <path>        Local PNG, JPEG, or WebP file to upload (required)
 *   --app-id <id>        Convex app id returned by Shots tools or .shots/app.json (required)
 *   --kind <kind>        app_screenshot | inspo | app_store_screenshot | icon | reference (default: reference)
 *   --locale <locale>    Optional App Store locale tag
 *   --base-url <url>     Shots app base URL (default: SHOTS_BASE_URL or https://shots.run)
 */

import fs from "node:fs/promises";
import path from "node:path";
import { parseArgs } from "node:util";

const VALID_KINDS = new Set([
  "app_screenshot",
  "inspo",
  "app_store_screenshot",
  "icon",
  "reference",
]);

const CONTENT_TYPES = new Map([
  [".png", "image/png"],
  [".jpg", "image/jpeg"],
  [".jpeg", "image/jpeg"],
  [".webp", "image/webp"],
]);

const { values: args } = parseArgs({
  options: {
    file: { type: "string" },
    "app-id": { type: "string" },
    kind: { type: "string", default: "reference" },
    locale: { type: "string" },
    "base-url": { type: "string" },
  },
});

function fail(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}

if (!args.file) fail("--file is required");
if (!args["app-id"]) fail("--app-id is required");
if (!VALID_KINDS.has(args.kind)) {
  fail(`--kind must be one of: ${Array.from(VALID_KINDS).join(", ")}`);
}

const filePath = path.resolve(args.file);
const ext = path.extname(filePath).toLowerCase();
const contentType = CONTENT_TYPES.get(ext);
if (!contentType) {
  fail("file must be .png, .jpg, .jpeg, or .webp");
}

let bytes;
try {
  bytes = await fs.readFile(filePath);
} catch (error) {
  fail(`could not read file: ${error instanceof Error ? error.message : String(error)}`);
}

const baseUrl = (args["base-url"] || process.env.SHOTS_BASE_URL || "https://shots.run")
  .replace(/\/$/, "");
const uploadUrl = `${baseUrl}/api/upload`;

const form = new FormData();
form.set("file", new Blob([bytes], { type: contentType }), path.basename(filePath));
form.set("appId", args["app-id"]);
form.set("kind", args.kind);
if (args.locale) form.set("locale", args.locale);

const response = await fetch(uploadUrl, {
  method: "POST",
  body: form,
});

const text = await response.text();
let payload;
try {
  payload = text ? JSON.parse(text) : {};
} catch {
  payload = { error: text };
}

if (!response.ok) {
  fail(payload.error || `upload failed with HTTP ${response.status}`);
}

console.log(JSON.stringify(payload, null, 2));
