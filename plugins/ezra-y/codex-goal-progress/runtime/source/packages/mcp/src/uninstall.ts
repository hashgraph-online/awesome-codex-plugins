import { spawn } from "node:child_process";
import { closeSync, mkdirSync, openSync } from "node:fs";
import { isAbsolute, resolve, sep } from "node:path";

export async function scheduleSourceUninstall(): Promise<{ code: string; statusFile: string }> {
  const home = process.env.GOAL_PROGRESS_CODEX_HOME;
  const bundle = process.env.GOAL_PROGRESS_SOURCE_BUNDLE;
  const data = process.env.GOAL_PROGRESS_PLUGIN_DATA;
  if (
    !home ||
    !isAbsolute(home) ||
    !data ||
    !isAbsolute(data) ||
    !bundle ||
    !isAbsolute(bundle) ||
    !resolve(bundle).startsWith(resolve(data, "source-runtime") + sep)
  ) {
    throw new Error("GOAL_PROGRESS_SOURCE_UNINSTALL_PATH_INVALID");
  }
  const logs = resolve(home, "logs");
  mkdirSync(logs, { recursive: true, mode: 0o700 });
  const statusFile = resolve(logs, "goal-progress-uninstall.log");
  const fd = openSync(statusFile, "a", 0o600);
  try {
    const child = spawn(process.execPath, [bundle, "__source-runtime-uninstall"], {
      detached: true,
      stdio: ["ignore", fd, fd],
      env: { ...process.env },
    });
    await new Promise<void>((ready, reject) => {
      child.once("spawn", ready);
      child.once("error", reject);
    });
    child.unref();
    return { code: "UNINSTALL_STARTED", statusFile };
  } finally {
    closeSync(fd);
  }
}
