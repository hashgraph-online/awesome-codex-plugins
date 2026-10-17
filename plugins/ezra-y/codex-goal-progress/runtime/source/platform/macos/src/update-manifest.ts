import {
  compareGoalProgressUpdateVersions,
  isGoalProgressUpdateVersion,
} from "../../../packages/contracts/src/update-state-runtime.js";

export const GOAL_PROGRESS_UPDATE_MANIFEST_MAX_BYTES = 16 * 1024;
export const GOAL_PROGRESS_MACOS_UPDATE_ASSET = "codex-goal-progress-macos-arm64.zip";
export const GOAL_PROGRESS_UPDATE_MANIFEST_URL =
  "https://github.com/Ezra-Y/codex-goal-progress/releases/latest/download/update-manifest.json";
const GOAL_PROGRESS_RELEASE_DOWNLOAD_PREFIX =
  "https://github.com/Ezra-Y/codex-goal-progress/releases/download";

export interface GoalProgressUpdateManifest {
  readonly schemaVersion: 1;
  readonly version: string;
  readonly asset: typeof GOAL_PROGRESS_MACOS_UPDATE_ASSET;
  readonly activation: "after-restart";
}

export function parseGoalProgressUpdateManifest(
  input: string | Uint8Array,
): GoalProgressUpdateManifest {
  const bytes = typeof input === "string" ? Buffer.byteLength(input) : input.byteLength;
  if (bytes > GOAL_PROGRESS_UPDATE_MANIFEST_MAX_BYTES) {
    throw new Error("GOAL_PROGRESS_UPDATE_MANIFEST_TOO_LARGE");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(typeof input === "string" ? input : Buffer.from(input).toString("utf8"));
  } catch {
    throw new Error("GOAL_PROGRESS_UPDATE_MANIFEST_INVALID");
  }
  if (
    parsed === null ||
    typeof parsed !== "object" ||
    Array.isArray(parsed) ||
    Object.keys(parsed).length !== 4 ||
    !("schemaVersion" in parsed) ||
    parsed.schemaVersion !== 1 ||
    !("version" in parsed) ||
    !isGoalProgressUpdateVersion(parsed.version) ||
    !("asset" in parsed) ||
    parsed.asset !== GOAL_PROGRESS_MACOS_UPDATE_ASSET ||
    !("activation" in parsed) ||
    parsed.activation !== "after-restart"
  ) {
    throw new Error("GOAL_PROGRESS_UPDATE_MANIFEST_INVALID");
  }
  return parsed as GoalProgressUpdateManifest;
}

export function compareGoalProgressVersions(left: string, right: string): -1 | 0 | 1 {
  return compareGoalProgressUpdateVersions(left, right);
}

export function goalProgressVersionedUpdateUrls(version: string): {
  readonly zip: string;
  readonly sha256Sums: string;
} {
  if (!isGoalProgressUpdateVersion(version)) {
    throw new Error("GOAL_PROGRESS_UPDATE_MANIFEST_INVALID");
  }
  const base = `${GOAL_PROGRESS_RELEASE_DOWNLOAD_PREFIX}/v${version}`;
  return {
    zip: `${base}/${GOAL_PROGRESS_MACOS_UPDATE_ASSET}`,
    sha256Sums: `${base}/SHA256SUMS`,
  };
}
