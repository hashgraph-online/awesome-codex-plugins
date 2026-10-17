import { createHash } from "node:crypto";
import { z } from "zod";
import { GOAL_PROGRESS_RELEASE_VERSION } from "../../contracts/src/index.js";
import { GOAL_PROGRESS_PAGE_HOST_VERSION } from "./page-host.js";

export const GOAL_PROGRESS_RENDERER_BUNDLE_FILE = "goal-progress.js";
export const GOAL_PROGRESS_RENDERER_BUNDLE_MAX_BYTES = 550_000;

export const GoalProgressRendererBundleManifestSchema = z
  .object({
    schemaVersion: z.literal(1),
    releaseVersion: z.string().trim().min(1).max(100),
    pageHostVersion: z.number().int().positive(),
    file: z.literal(GOAL_PROGRESS_RENDERER_BUNDLE_FILE),
    bytes: z.number().int().positive().max(GOAL_PROGRESS_RENDERER_BUNDLE_MAX_BYTES),
    sha256: z.string().regex(/^[a-f0-9]{64}$/u),
  })
  .strict();

export type GoalProgressRendererBundleManifest = z.infer<
  typeof GoalProgressRendererBundleManifestSchema
>;

export interface GoalProgressRendererBundle {
  readonly source: string;
  readonly manifest: GoalProgressRendererBundleManifest;
}

function bundleError(code: string, detail?: string): Error {
  return new Error(detail ? `${code}: ${detail}` : code);
}

export function createGoalProgressRendererBundle(
  source: string,
  manifestInput: unknown,
): GoalProgressRendererBundle {
  const manifest = GoalProgressRendererBundleManifestSchema.parse(manifestInput);
  if (manifest.releaseVersion !== GOAL_PROGRESS_RELEASE_VERSION) {
    throw bundleError("GOAL_PROGRESS_RENDERER_BUNDLE_RELEASE_MISMATCH", manifest.releaseVersion);
  }
  if (manifest.pageHostVersion !== GOAL_PROGRESS_PAGE_HOST_VERSION) {
    throw bundleError(
      "GOAL_PROGRESS_RENDERER_BUNDLE_VERSION_MISMATCH",
      String(manifest.pageHostVersion),
    );
  }
  const bytes = Buffer.byteLength(source);
  if (
    bytes === 0 ||
    bytes > GOAL_PROGRESS_RENDERER_BUNDLE_MAX_BYTES ||
    source.includes("\0") ||
    bytes !== manifest.bytes
  ) {
    throw bundleError("GOAL_PROGRESS_RENDERER_BUNDLE_BYTES_MISMATCH", String(bytes));
  }
  const sha256 = createHash("sha256").update(source).digest("hex");
  if (sha256 !== manifest.sha256) {
    throw bundleError("GOAL_PROGRESS_RENDERER_BUNDLE_SHA256_MISMATCH");
  }
  return Object.freeze({
    source,
    manifest: Object.freeze(manifest),
  });
}

export function assertGoalProgressRendererBundle(
  bundle: GoalProgressRendererBundle,
): GoalProgressRendererBundle {
  return createGoalProgressRendererBundle(bundle.source, bundle.manifest);
}
