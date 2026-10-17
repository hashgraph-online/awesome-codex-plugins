import { spawn } from "node:child_process";

export const GOAL_PROGRESS_PLUGIN_ID = "codex-goal-progress@codex-goal-progress-local";
const HOOK_CONFIGURATION_TIMEOUT_MS = 10_000;
const GOAL_PROGRESS_HOOK_KEYS = [
  `${GOAL_PROGRESS_PLUGIN_ID}:hooks/hooks.json:pre_tool_use:0:0`,
  `${GOAL_PROGRESS_PLUGIN_ID}:hooks/hooks.json:post_tool_use:0:0`,
  `${GOAL_PROGRESS_PLUGIN_ID}:hooks/hooks.json:session_start:0:0`,
] as const;

interface CodexHookMetadata {
  readonly key: string;
  readonly pluginId: string | null;
  readonly currentHash: string;
  readonly enabled: boolean;
  readonly trustStatus: string;
}

interface CodexHooksListResponse {
  readonly data: ReadonlyArray<{
    readonly hooks: readonly CodexHookMetadata[];
  }>;
}

function quotedKeyPathSegment(value: string): string {
  return `"${value.replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"`;
}

async function configureInstalledGoalProgressHooks(
  command: string,
  codexHomeDirectory: string,
  mode: "enable" | "remove",
): Promise<void> {
  const child = spawn(command, ["app-server", "--stdio"], {
    env: {
      ...process.env,
      CODEX_HOME: codexHomeDirectory,
    },
    stdio: ["pipe", "pipe", "pipe"],
  });
  child.stdout.setEncoding("utf8");
  child.stderr.setEncoding("utf8");

  await new Promise<void>((resolveEnable, rejectEnable) => {
    let settled = false;
    let stdoutBuffer = "";
    let stderr = "";
    const finish = (error?: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      child.kill("SIGTERM");
      if (error) {
        rejectEnable(error);
      } else {
        resolveEnable();
      }
    };
    const send = (message: unknown) => {
      child.stdin.write(`${JSON.stringify(message)}\n`);
    };
    const requestHooks = (id: number) => {
      send({
        id,
        method: "hooks/list",
        params: { cwds: [codexHomeDirectory] },
      });
    };
    const timeout = setTimeout(
      () => finish(new Error("GOAL_PROGRESS_HOOK_ENABLE_TIMEOUT")),
      HOOK_CONFIGURATION_TIMEOUT_MS,
    );

    child.stderr.on("data", (chunk: string) => {
      stderr = `${stderr}${chunk}`.slice(-2_000);
    });
    child.once("error", (error) => finish(error));
    child.once("exit", (code) => {
      if (!settled) {
        finish(
          new Error(
            `GOAL_PROGRESS_HOOK_ENABLE_APP_SERVER_EXITED: code=${code ?? "signal"}; ${stderr}`,
          ),
        );
      }
    });
    child.stdout.on("data", (chunk: string) => {
      stdoutBuffer += chunk;
      let newlineIndex = stdoutBuffer.indexOf("\n");
      while (newlineIndex >= 0) {
        const line = stdoutBuffer.slice(0, newlineIndex).trim();
        stdoutBuffer = stdoutBuffer.slice(newlineIndex + 1);
        newlineIndex = stdoutBuffer.indexOf("\n");
        if (!line) {
          continue;
        }
        let message: {
          readonly id?: number;
          readonly result?: unknown;
          readonly error?: { readonly message?: string };
        };
        try {
          message = JSON.parse(line) as typeof message;
        } catch {
          continue;
        }
        if (message.error) {
          finish(
            new Error(
              `GOAL_PROGRESS_HOOK_ENABLE_APP_SERVER_ERROR: ${message.error.message ?? "unknown"}`,
            ),
          );
          return;
        }
        if (message.id === 1) {
          send({ method: "initialized", params: {} });
          if (mode === "enable") {
            requestHooks(2);
          } else {
            send({
              id: 5,
              method: "config/batchWrite",
              params: {
                edits: GOAL_PROGRESS_HOOK_KEYS.map((key) => ({
                  keyPath: `hooks.state.${quotedKeyPathSegment(key)}`,
                  value: null,
                  mergeStrategy: "replace",
                })),
                reloadUserConfig: true,
              },
            });
          }
          continue;
        }
        if (message.id === 2) {
          const listed = message.result as CodexHooksListResponse;
          const hooks = listed.data
            .flatMap((entry) => entry.hooks)
            .filter((hook) => hook.pluginId === GOAL_PROGRESS_PLUGIN_ID);
          if (
            hooks.length === 0 ||
            hooks.some((hook) => !/^sha256:[0-9a-f]{64}$/u.test(hook.currentHash))
          ) {
            finish(new Error("GOAL_PROGRESS_HOOK_ENABLE_LIST_INVALID"));
            return;
          }
          send({
            id: 3,
            method: "config/batchWrite",
            params: {
              edits: hooks.flatMap((hook) => {
                const statePath = `hooks.state.${quotedKeyPathSegment(hook.key)}`;
                return [
                  {
                    keyPath: `${statePath}.trusted_hash`,
                    value: hook.currentHash,
                    mergeStrategy: "upsert",
                  },
                  {
                    keyPath: `${statePath}.enabled`,
                    value: true,
                    mergeStrategy: "upsert",
                  },
                ];
              }),
              reloadUserConfig: true,
            },
          });
          continue;
        }
        if (message.id === 3) {
          requestHooks(4);
          continue;
        }
        if (message.id === 4) {
          const listed = message.result as CodexHooksListResponse;
          const hooks = listed.data
            .flatMap((entry) => entry.hooks)
            .filter((hook) => hook.pluginId === GOAL_PROGRESS_PLUGIN_ID);
          if (
            hooks.length === 0 ||
            hooks.some((hook) => !hook.enabled || hook.trustStatus !== "trusted")
          ) {
            finish(new Error("GOAL_PROGRESS_HOOK_ENABLE_VERIFY_FAILED"));
            return;
          }
          finish();
          return;
        }
        if (message.id === 5) {
          finish();
          return;
        }
      }
    });

    send({
      id: 1,
      method: "initialize",
      params: {
        clientInfo: {
          name: "codex-goal-progress-installer",
          version: "1",
        },
        capabilities: {
          experimentalApi: true,
        },
      },
    });
  });
}

export async function enableInstalledGoalProgressHooks(
  command: string,
  codexHomeDirectory: string,
): Promise<void> {
  await configureInstalledGoalProgressHooks(command, codexHomeDirectory, "enable");
}

export async function removeInstalledGoalProgressHookState(
  command: string,
  codexHomeDirectory: string,
): Promise<void> {
  await configureInstalledGoalProgressHooks(command, codexHomeDirectory, "remove");
}
