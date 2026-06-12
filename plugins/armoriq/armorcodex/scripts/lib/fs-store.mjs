import { mkdir, readFile, rename, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

export async function readJson(filePath, fallbackValue) {
  try {
    const raw = await readFile(filePath, "utf8");
    return JSON.parse(raw);
  } catch (error) {
    if (error && typeof error === "object" && error.code === "ENOENT") {
      return fallbackValue;
    }
    // Corrupted JSON (e.g. interrupted write from an older non-atomic build)
    // falls back to the default rather than breaking the whole session.
    if (error instanceof SyntaxError) {
      return fallbackValue;
    }
    throw error;
  }
}

// Atomic write: write to a sibling tmp file then rename into place. Prevents
// partial/torn JSON when two hooks (PreToolUse + PostToolUse) race or when the
// process is killed mid-write.
export async function writeJson(filePath, value) {
  await mkdir(path.dirname(filePath), { recursive: true });
  const tmpPath = `${filePath}.tmp.${process.pid}.${Date.now()}`;
  const payload = JSON.stringify(value, null, 2);
  try {
    await writeFile(tmpPath, payload, "utf8");
    await rename(tmpPath, filePath);
  } catch (error) {
    await unlink(tmpPath).catch(() => {});
    throw error;
  }
}

