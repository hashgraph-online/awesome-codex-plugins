import { chmod, mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const INSTALLED_BINARY =
  "$HOME/Library/Application Support/CodexGoalProgress/install/current/bin/goal-progress";
export const GOAL_PROGRESS_STABLE_HOOK_COMMAND =
  '/bin/sh -c \'p="$HOME/Library/Application Support/CodexGoalProgress/install/current/bin/goal-progress"; [ -x "$p" ] || exit 0; exec "$p" hook\'';
export const GOAL_PROGRESS_STABLE_MCP_LAUNCHER = [
  "#!/bin/sh",
  "set -eu",
  `binary="${INSTALLED_BINARY}"`,
  'if [ ! -x "$binary" ]; then',
  '  echo "GOAL_PROGRESS_UNINSTALLED_OR_DISABLED: run goal-progress install --json" >&2',
  "  exit 1",
  "fi",
  'exec "$binary" mcp-server "$@"',
  "",
].join("\n");
export const GOAL_PROGRESS_STABLE_HOOK_LAUNCHER = [
  "#!/bin/sh",
  `binary="${INSTALLED_BINARY}"`,
  '[ -x "$binary" ] || exit 0',
  'exec "$binary" hook "$@"',
  "",
].join("\n");

export interface ReleasePluginRuntimeFiles {
  readonly mcpJson: string;
  readonly hooksJson: string;
  readonly mcpLauncher: string;
  readonly hookLauncher: string;
}

function record(value: unknown, code: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(code);
  }
  return value as Record<string, unknown>;
}

export function createReleaseMarketplaceManifest(sourceMarketplace: unknown): string {
  const code = "GOAL_PROGRESS_RELEASE_MARKETPLACE_INVALID";
  const marketplace = structuredClone(record(sourceMarketplace, code));
  if (!Array.isArray(marketplace.plugins)) throw new Error(code);
  const plugin = marketplace.plugins.find(
    (entry: unknown) => record(entry, code).name === "codex-goal-progress",
  );
  if (!plugin) throw new Error(code);
  const source = record(record(plugin, code).source, code);
  if (source.source !== "local") throw new Error(code);
  source.path = "./plugins/codex-goal-progress";
  return `${JSON.stringify(marketplace, null, 2)}\n`;
}

export function createReleasePluginManifest(sourceManifest: unknown): string {
  const manifest = structuredClone(record(sourceManifest, "GOAL_PROGRESS_PLUGIN_MANIFEST_INVALID"));
  delete manifest.scripts;
  return `${JSON.stringify(manifest, null, 2)}\n`;
}

export function createReleasePluginRuntimeFiles(
  sourceMcp: unknown,
  sourceHooks: unknown,
): ReleasePluginRuntimeFiles {
  const mcp = structuredClone(record(sourceMcp, "GOAL_PROGRESS_PLUGIN_MCP_INVALID"));
  const server = record(mcp.goal_progress, "GOAL_PROGRESS_PLUGIN_MCP_INVALID");
  server.command = "./bin/goal-progress-mcp";
  server.args = [];
  server.cwd = ".";
  delete server.startup_timeout_sec;
  delete server.startup_timeout_ms;

  const hooksDocument = structuredClone(record(sourceHooks, "GOAL_PROGRESS_PLUGIN_HOOKS_INVALID"));
  const hooks = record(hooksDocument.hooks, "GOAL_PROGRESS_PLUGIN_HOOKS_INVALID");
  if ("UserPromptSubmit" in hooks) {
    throw new Error("GOAL_PROGRESS_PLUGIN_USER_PROMPT_HOOK_FORBIDDEN");
  }
  for (const groupsValue of Object.values(hooks)) {
    if (!Array.isArray(groupsValue)) {
      throw new Error("GOAL_PROGRESS_PLUGIN_HOOKS_INVALID");
    }
    for (const groupValue of groupsValue) {
      const group = record(groupValue, "GOAL_PROGRESS_PLUGIN_HOOKS_INVALID");
      if (!Array.isArray(group.hooks)) {
        throw new Error("GOAL_PROGRESS_PLUGIN_HOOKS_INVALID");
      }
      for (const hookValue of group.hooks) {
        const hook = record(hookValue, "GOAL_PROGRESS_PLUGIN_HOOKS_INVALID");
        if (hook.type !== "command") {
          throw new Error("GOAL_PROGRESS_PLUGIN_HOOK_TYPE_INVALID");
        }
        hook.command = GOAL_PROGRESS_STABLE_HOOK_COMMAND;
      }
    }
  }

  return {
    mcpJson: `${JSON.stringify(mcp, null, 2)}\n`,
    hooksJson: `${JSON.stringify(hooksDocument, null, 2)}\n`,
    mcpLauncher: GOAL_PROGRESS_STABLE_MCP_LAUNCHER,
    hookLauncher: GOAL_PROGRESS_STABLE_HOOK_LAUNCHER,
  };
}

export async function writeReleasePluginRuntimeFiles(
  pluginRoot: string,
  files: ReleasePluginRuntimeFiles,
): Promise<void> {
  const mcpLauncherPath = resolve(pluginRoot, "bin/goal-progress-mcp");
  const hookLauncherPath = resolve(pluginRoot, "bin/goal-progress-hook");
  await mkdir(resolve(pluginRoot, "bin"), { recursive: true });
  await Promise.all([
    writeFile(resolve(pluginRoot, ".mcp.json"), files.mcpJson),
    writeFile(resolve(pluginRoot, "hooks/hooks.json"), files.hooksJson),
    writeFile(mcpLauncherPath, files.mcpLauncher),
    writeFile(hookLauncherPath, files.hookLauncher),
  ]);
  await Promise.all([chmod(mcpLauncherPath, 0o700), chmod(hookLauncherPath, 0o700)]);
}
