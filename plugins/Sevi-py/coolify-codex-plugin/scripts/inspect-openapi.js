#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const spec = JSON.parse(readFileSync(resolve(__dirname, "../data/openapi-index.json"), "utf8"));

for (const [path, methods] of Object.entries(spec.paths || {})) {
  for (const [method, operation] of Object.entries(methods)) {
    const summary = operation.summary ? ` - ${operation.summary}` : "";
    console.log(`${method.toUpperCase()} ${path}${summary}`);
  }
}
