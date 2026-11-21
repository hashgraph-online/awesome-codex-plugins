#!/usr/bin/env node
import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { chmod, lstat, mkdir, rm } from "node:fs/promises";
import net from "node:net";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import readline from "node:readline";
import { fileURLToPath } from "node:url";
import { StartupListenerBridge } from "./startup-listener-bridge.mjs";

const [bundleId, appPath, executablePath] = process.argv.slice(2);
if (!bundleId || !appPath || !executablePath) {
  process.stderr.write("usage: startup-listener.mjs <bundle-id> <app-path> <executable-path>\n");
  process.exit(64);
}

const scriptPath = resolve(dirname(fileURLToPath(import.meta.url)), "startup-listener.jxa");
const uid = process.getuid?.();
if (!Number.isSafeInteger(uid) || uid < 0) {
  throw new Error("GOAL_PROGRESS_STARTUP_LISTENER_UID_UNAVAILABLE");
}
const socketRoot =
  process.platform === "darwin" ? `/tmp/cgp-${uid}` : resolve(tmpdir(), `cgp-${uid}`);
try {
  await mkdir(socketRoot, { mode: 0o700 });
} catch (error) {
  if (!(error instanceof Error && "code" in error && error.code === "EEXIST")) {
    throw error;
  }
}
const socketRootMetadata = await lstat(socketRoot);
if (
  !socketRootMetadata.isDirectory() ||
  socketRootMetadata.isSymbolicLink() ||
  socketRootMetadata.uid !== uid
) {
  throw new Error("GOAL_PROGRESS_STARTUP_LISTENER_SOCKET_ROOT_INVALID");
}
await chmod(socketRoot, 0o700);
const socketPath = resolve(socketRoot, `s-${process.pid}-${randomUUID().slice(0, 8)}.sock`);
await rm(socketPath, { force: true });

let shuttingDown = false;

const bridge = new StartupListenerBridge({
  continueProcess(pid) {
    try {
      process.kill(pid, "SIGCONT");
    } catch {
      // The intercepted process may already have exited.
    }
  },
});

const server = net.createServer((connection) => {
  bridge.acceptConnection(connection);
});
server.on("error", (error) => {
  if (!shuttingDown) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  }
  bridge.release();
});
await new Promise((resolveListen, rejectListen) => {
  server.once("error", rejectListen);
  server.listen(socketPath, async () => {
    server.off("error", rejectListen);
    try {
      await chmod(socketPath, 0o600);
      resolveListen();
    } catch (error) {
      rejectListen(error);
    }
  });
});

const child = spawn(
  "/usr/bin/osascript",
  ["-l", "JavaScript", scriptPath, bundleId, appPath, executablePath, socketPath],
  {
    stdio: ["ignore", "pipe", "pipe"],
  },
);
child.stderr.on("data", (chunk) => process.stderr.write(chunk));

const childLines = readline.createInterface({ input: child.stdout });
childLines.on("line", (line) => {
  let event;
  try {
    event = JSON.parse(line);
  } catch {
    return;
  }
  if (event?.event === "codex.willLaunch" && Number.isSafeInteger(event.pid)) {
    bridge.acceptLaunch(event.pid);
  }
  process.stdout.write(`${line}\n`);
});

const parentLines = readline.createInterface({ input: process.stdin });
parentLines.on("line", (line) => {
  let response;
  try {
    response = JSON.parse(line);
  } catch {
    return;
  }
  bridge.acceptResponse(response);
});

async function shutdown(exitCode = 0) {
  if (shuttingDown) {
    return;
  }
  shuttingDown = true;
  bridge.close();
  parentLines.close();
  childLines.close();
  if (child.exitCode === null && child.signalCode === null) {
    child.kill("SIGTERM");
  }
  if (server.listening) {
    await new Promise((resolveClose) => server.close(resolveClose));
  }
  await rm(socketPath, { force: true }).catch(() => undefined);
  process.exitCode = exitCode;
}

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => void shutdown(0));
}
parentLines.on("close", () => void shutdown(0));
child.on("exit", (code, signal) => {
  if (!shuttingDown && code !== 0) {
    process.stderr.write(`GOAL_PROGRESS_STARTUP_LISTENER_EXITED: code=${code}; signal=${signal}\n`);
  }
  void shutdown(code === 0 ? 0 : 1);
});
