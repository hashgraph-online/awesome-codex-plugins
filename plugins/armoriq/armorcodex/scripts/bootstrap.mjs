// Lazily install npm dependencies on first run, then dispatch to the
// real hook-router or MCP server. This makes the plugin work after
// `codex plugin install` or repo-local hook setup even when the plugin
// directory has no node_modules.
import { existsSync, writeFileSync, readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.dirname(__dirname);
const installedMarker = path.join(pluginRoot, "node_modules", ".armorcodex-installed");
const packageFiles = [
  path.join(pluginRoot, "node_modules", "@armoriq", "sdk", "package.json"),
  path.join(pluginRoot, "node_modules", "zod", "package.json"),
  path.join(pluginRoot, "node_modules", "@modelcontextprotocol", "sdk", "package.json"),
];

// The marker is only trusted when all expected packages are also present.
// Partial installs (e.g. zod present, sdk missing) would previously pass
// the per-file check and the dispatch would crash on a missing import.
function installedOk() {
  if (!existsSync(installedMarker)) return false;
  if (!packageFiles.every(existsSync)) return false;
  try {
    const markerVersion = readFileSync(installedMarker, "utf8").trim();
    const pkg = JSON.parse(
      readFileSync(path.join(pluginRoot, "package.json"), "utf8")
    );
    return markerVersion === pkg.version;
  } catch {
    return false;
  }
}

if (!installedOk()) {
  process.stderr.write("[armorcodex] installing dependencies (one-time)...\n");
  const result = spawnSync("npm", ["install", "--omit=dev", "--silent", "--no-audit", "--no-fund"], {
    cwd: pluginRoot,
    stdio: ["ignore", "ignore", "inherit"]
  });
  if (result.status !== 0) {
    process.stderr.write("[armorcodex] npm install failed (exit " + result.status + ")\n");
    process.exit(1);
  }
  try {
    const pkg = JSON.parse(
      readFileSync(path.join(pluginRoot, "package.json"), "utf8")
    );
    writeFileSync(installedMarker, pkg.version || "ok", "utf8");
  } catch {
    // best-effort — if we can't write the marker the next run will reinstall
  }
}

// MCP servers and hook routers communicate with Codex via JSON-RPC / JSON
// over stdio. Any non-JSON write to stdout corrupts the protocol and Codex
// closes the transport. Redirect console.* to stderr so dependencies (the
// ArmorIQ SDK in particular) can't accidentally pollute the channel.
const _consoleRedirect = (...a) => {
  const line = a
    .map((x) => (typeof x === "string" ? x : JSON.stringify(x, null, 0)))
    .join(" ");
  process.stderr.write(line + "\n");
};
for (const m of ["log", "info", "warn", "error", "debug", "trace"]) {
  console[m] = _consoleRedirect;
}

const target = process.argv[2];
if (target === "router") {
  await import("./hook-router.mjs");
} else if (target === "mcp") {
  await import("./policy-mcp.mjs");
} else {
  process.stderr.write("[armorcodex] bootstrap: unknown target '" + target + "'\n");
  process.exit(2);
}
