import { execFileSync, spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

// Canonical launcher; scripts/sync-agent-launchers.mjs copies it into each skill.
function readRequest() {
  try {
    if (process.argv.length > 3) throw new Error();
    const request = JSON.parse(fs.readFileSync(process.argv[2] ?? 0, "utf8"));
    if (!request || typeof request !== "object" || Array.isArray(request) ||
        typeof request.package_dir !== "string" || !path.isAbsolute(request.package_dir) ||
        request.package_dir.includes("\0") || !Array.isArray(request.argv) || !request.argv.length ||
        !request.argv.every((arg) => typeof arg === "string" && !arg.includes("\0"))) {
      throw new Error();
    }
    if (request.integration !== undefined &&
        !["source", "name", "version"].every((key) =>
          typeof request.integration?.[key] === "string" && /^[A-Za-z0-9_.+-]+$/.test(request.integration[key]))) {
      throw new Error();
    }
    return request;
  } catch {
    throw new Error("Invalid agent request. Supply a JSON object with an absolute package_dir and a nonempty string argv array.");
  }
}

function verifyEntry(packageDir) {
  let entry;
  try {
    const root = fs.realpathSync(packageDir);
    const manifest = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
    if (manifest.name !== "@call-e/cli" || !/^(?:\.\/)?bin\/calle\.js$/.test(manifest.bin?.calle ?? "")) {
      throw new Error();
    }
    entry = fs.realpathSync(path.join(root, "bin", "calle.js"));
    if (entry !== path.join(root, "bin", "calle.js")) throw new Error();
  } catch {
    throw new Error("MCP package identity or entry check failed. Select a trusted @call-e/cli installation.");
  }

  const checks = [
    [["--help"], ["auth login", "call plan", "call run", "call recover", "next_argv"]],
    [["auth", "login", "--help"], ["Usage: calle auth login", "--broker-base-url"]],
    [["call", "plan", "--help"], ["Usage: calle call plan", "--to-phone", "--goal"]],
    [["call", "run", "--help"], ["Usage: calle call run", "--plan-id", "--confirm-token"]],
    [["call", "recover", "--help"], ["Usage: calle call recover", "--recovery-id"]],
  ];
  try {
    for (const [argv, required] of checks) {
      // Probes receive no request values or inherited credentials.
      const help = execFileSync(process.execPath, [entry, ...argv], {
        shell: false,
        encoding: "utf8",
        timeout: 10000,
        maxBuffer: 1024 * 1024,
        stdio: ["ignore", "pipe", "pipe"],
        env: { ...(process.env.SystemRoot ? { SystemRoot: process.env.SystemRoot } : {}), DO_NOT_TRACK: "1" },
      });
      if (!required.every((text) => help.includes(text))) throw new Error();
    }
  } catch {
    throw new Error("MCP command help check failed. Update the trusted @call-e/cli installation before authentication.");
  }
  return entry;
}

try {
  const request = readRequest();
  const entry = verifyEntry(request.package_dir);
  const child = spawn(process.execPath, [entry, ...request.argv], {
    shell: false,
    stdio: ["ignore", "inherit", "inherit"],
    env: {
      ...process.env,
      CALLE_SOURCE: request.integration?.source ?? "",
      CALLE_INTEGRATION: request.integration?.name ?? "",
      CALLE_INTEGRATION_VERSION: request.integration?.version ?? "",
    },
  });
  process.once("SIGINT", () => child.kill("SIGINT"));
  process.once("SIGTERM", () => child.kill("SIGTERM"));
  child.on("error", () => {
    process.stderr.write("Verified MCP CLI could not start.\n");
    process.exitCode = 1;
  });
  child.on("exit", (code, signal) => {
    process.exitCode = code ?? 1;
    if (signal) process.stderr.write("MCP CLI was interrupted; check call recovery before retrying.\n");
  });
} catch (error) {
  process.stderr.write(error.message + "\n");
  process.exitCode = 1;
}
