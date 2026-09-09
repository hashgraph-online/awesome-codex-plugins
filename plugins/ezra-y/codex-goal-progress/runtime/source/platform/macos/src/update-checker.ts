import {
  GOAL_PROGRESS_UPDATE_MANIFEST_MAX_BYTES,
  GOAL_PROGRESS_UPDATE_MANIFEST_URL,
  type GoalProgressUpdateManifest,
  parseGoalProgressUpdateManifest,
} from "./update-manifest.js";

export const GOAL_PROGRESS_UPDATE_CHECK_TIMEOUT_MS = 15_000;

export interface CheckGoalProgressUpdateOptions {
  readonly fetchImpl?: typeof fetch;
  readonly timeoutMs?: number;
}

function safeRedirectUrl(value: string): boolean {
  if (!value) {
    return true;
  }
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      url.username === "" &&
      url.password === "" &&
      (url.hostname === "github.com" || url.hostname.endsWith(".githubusercontent.com"))
    );
  } catch {
    return false;
  }
}

async function readBoundedBody(response: Response): Promise<Uint8Array> {
  const declared = response.headers.get("content-length");
  if (declared !== null) {
    const bytes = Number(declared);
    if (
      !Number.isSafeInteger(bytes) ||
      bytes < 0 ||
      bytes > GOAL_PROGRESS_UPDATE_MANIFEST_MAX_BYTES
    ) {
      throw new Error("GOAL_PROGRESS_UPDATE_MANIFEST_TOO_LARGE");
    }
  }
  if (!response.body) {
    return new Uint8Array();
  }
  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let bytes = 0;
  while (true) {
    const chunk = await reader.read();
    if (chunk.done) {
      break;
    }
    bytes += chunk.value.byteLength;
    if (bytes > GOAL_PROGRESS_UPDATE_MANIFEST_MAX_BYTES) {
      await reader.cancel().catch(() => undefined);
      throw new Error("GOAL_PROGRESS_UPDATE_MANIFEST_TOO_LARGE");
    }
    chunks.push(chunk.value);
  }
  const result = new Uint8Array(bytes);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return result;
}

export async function checkGoalProgressUpdateManifest(
  options: CheckGoalProgressUpdateOptions = {},
): Promise<GoalProgressUpdateManifest> {
  const fetchImpl = options.fetchImpl ?? globalThis.fetch;
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? GOAL_PROGRESS_UPDATE_CHECK_TIMEOUT_MS,
  );
  timeout.unref?.();
  try {
    const response = await fetchImpl(GOAL_PROGRESS_UPDATE_MANIFEST_URL, {
      signal: controller.signal,
      redirect: "follow",
      headers: { accept: "application/json" },
    });
    if (!safeRedirectUrl(response.url)) {
      throw new Error("GOAL_PROGRESS_UPDATE_REDIRECT_UNSAFE");
    }
    if (!response.ok) {
      throw new Error("GOAL_PROGRESS_UPDATE_CHECK_HTTP_FAILED");
    }
    return parseGoalProgressUpdateManifest(await readBoundedBody(response));
  } catch (error) {
    if (controller.signal.aborted || (error instanceof Error && error.name === "AbortError")) {
      throw new Error("GOAL_PROGRESS_UPDATE_CHECK_TIMEOUT");
    }
    if (
      error instanceof Error &&
      /^GOAL_PROGRESS_UPDATE_(?:CHECK_HTTP_FAILED|MANIFEST_TOO_LARGE|MANIFEST_INVALID|REDIRECT_UNSAFE)$/u.test(
        error.message,
      )
    ) {
      throw error;
    }
    throw new Error("GOAL_PROGRESS_UPDATE_CHECK_HTTP_FAILED");
  } finally {
    clearTimeout(timeout);
  }
}
