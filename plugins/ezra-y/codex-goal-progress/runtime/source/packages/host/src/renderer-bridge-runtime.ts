import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  inspectCodexMacosApp,
  readCodexCdpRuntimeState,
  verifyCodexCdpListenerOwnership,
} from "../../../platform/macos/src/index.js";
import {
  CdpProtocolClient,
  type CodexCdpTarget,
  connectGoalProgressRendererBridge,
  connectGoalProgressRendererBridgeTarget,
  createGoalProgressRendererBundle,
  discoverCodexCdp,
  GoalProgressCdpViewClient,
  type GoalProgressRendererBridge,
} from "../../codex-adapter/src/index.js";
import { GoalProgressRendererTargetIdSchema } from "../../ipc/src/index.js";
import type { GoalProgressPaths } from "../../store/src/index.js";
import type { RendererBridgeSupervisorConnection } from "./renderer-bridge-supervisor.js";
import type { RendererTargetInfo, RendererTargetSource } from "./renderer-target-manager.js";

interface BrowserTargetInfo {
  readonly targetId: string;
  readonly type: string;
  readonly url: string;
}

export interface RendererTargetBrowserClient {
  onEvent(method: string, listener: (params: unknown) => void): () => void;
  onFailure?(listener: (error: Error) => void): () => void;
  send(method: string, params?: unknown): Promise<unknown>;
  close(): Promise<void>;
}

export interface BrowserTargetSourceOptions {
  readonly port: number;
  readonly browserClient: RendererTargetBrowserClient;
  readonly initialTargets: readonly CodexCdpTarget[];
  readonly connectTarget: (target: CodexCdpTarget) => Promise<RendererBridgeSupervisorConnection>;
}

function rendererTargetInfo(input: unknown): BrowserTargetInfo | null {
  if (
    input === null ||
    typeof input !== "object" ||
    !("targetId" in input) ||
    !("type" in input) ||
    !("url" in input) ||
    !GoalProgressRendererTargetIdSchema.safeParse(input.targetId).success ||
    typeof input.type !== "string" ||
    typeof input.url !== "string"
  ) {
    return null;
  }
  return {
    targetId: input.targetId as string,
    type: input.type,
    url: input.url,
  };
}

function destroyedTargetId(input: unknown): string | null {
  if (
    input === null ||
    typeof input !== "object" ||
    !("targetId" in input) ||
    !GoalProgressRendererTargetIdSchema.safeParse(input.targetId).success
  ) {
    return null;
  }
  return input.targetId as string;
}

class BrowserRendererTargetSource implements RendererTargetSource {
  readonly #port: number;
  readonly #browserClient: RendererTargetBrowserClient;
  readonly #connect: BrowserTargetSourceOptions["connectTarget"];
  readonly #known = new Map<string, RendererTargetInfo>();
  readonly #infoListeners = new Set<(target: RendererTargetInfo) => void>();
  readonly #destroyedListeners = new Set<(targetId: string) => void>();
  readonly #failureListeners = new Set<(error: Error) => void>();
  readonly #removeEventListeners: (() => void)[];
  #closed = false;
  #failed: Error | undefined;

  constructor(options: BrowserTargetSourceOptions) {
    this.#port = options.port;
    this.#browserClient = options.browserClient;
    this.#connect = options.connectTarget;
    for (const target of options.initialTargets) {
      this.#known.set(target.id, {
        targetId: target.id,
        type: target.type,
        url: target.url,
      });
    }
    const removeFailureListener = this.#browserClient.onFailure?.((error) => {
      this.#receiveFailure(error);
    });
    this.#removeEventListeners = [
      this.#browserClient.onEvent("Target.targetCreated", (params) => {
        this.#receiveInfo(
          params && typeof params === "object" && "targetInfo" in params ? params.targetInfo : null,
        );
      }),
      this.#browserClient.onEvent("Target.targetInfoChanged", (params) => {
        this.#receiveInfo(
          params && typeof params === "object" && "targetInfo" in params ? params.targetInfo : null,
        );
      }),
      this.#browserClient.onEvent("Target.targetDestroyed", (params) => {
        const targetId = destroyedTargetId(params);
        if (!targetId) {
          return;
        }
        this.#known.delete(targetId);
        for (const listener of this.#destroyedListeners) {
          listener(targetId);
        }
      }),
      ...(removeFailureListener ? [removeFailureListener] : []),
    ];
  }

  get initialTargets(): readonly RendererTargetInfo[] {
    return [...this.#known.values()];
  }

  onTargetInfo(listener: (target: RendererTargetInfo) => void): () => void {
    this.#infoListeners.add(listener);
    return () => this.#infoListeners.delete(listener);
  }

  onTargetDestroyed(listener: (targetId: string) => void): () => void {
    this.#destroyedListeners.add(listener);
    return () => this.#destroyedListeners.delete(listener);
  }

  onFailure(listener: (error: Error) => void): () => void {
    this.#failureListeners.add(listener);
    if (this.#failed) {
      try {
        listener(this.#failed);
      } catch {
        // Failure observers cannot change the existing browser transport failure.
      }
    }
    return () => this.#failureListeners.delete(listener);
  }

  async connectTarget(target: RendererTargetInfo): Promise<RendererBridgeSupervisorConnection> {
    if (
      this.#closed ||
      this.#failed ||
      !GoalProgressRendererTargetIdSchema.safeParse(target.targetId).success
    ) {
      throw new Error("RENDERER_TARGET_UNKNOWN");
    }
    const webSocketDebuggerUrl = `ws://127.0.0.1:${this.#port}/devtools/page/${target.targetId}`;
    return this.#connect({
      id: target.targetId,
      type: target.type,
      title: "",
      url: target.url,
      webSocketDebuggerUrl,
    });
  }

  async close(): Promise<void> {
    if (this.#closed) {
      return;
    }
    this.#closed = true;
    for (const remove of this.#removeEventListeners) {
      remove();
    }
    this.#infoListeners.clear();
    this.#destroyedListeners.clear();
    this.#failureListeners.clear();
    await this.#browserClient
      .send("Target.setDiscoverTargets", { discover: false })
      .catch(() => undefined);
    await this.#browserClient.close();
  }

  #receiveInfo(input: unknown): void {
    const target = rendererTargetInfo(input);
    if (!target || this.#closed || this.#failed) {
      return;
    }
    this.#known.set(target.targetId, target);
    for (const listener of this.#infoListeners) {
      listener(target);
    }
  }

  #receiveFailure(error: Error): void {
    if (this.#closed || this.#failed) {
      return;
    }
    this.#failed = error;
    for (const listener of this.#failureListeners) {
      try {
        listener(error);
      } catch {
        // One observer cannot block the other recovery observers.
      }
    }
  }
}

export function createBrowserRendererTargetSource(
  options: BrowserTargetSourceOptions,
): RendererTargetSource {
  return new BrowserRendererTargetSource(options);
}

export interface ResolveHelperRendererBundleDirectoryOptions {
  readonly configuredDirectory?: string;
  readonly executablePath?: string;
  readonly moduleUrl?: string | undefined;
}

export async function resolveHelperRendererBundleDirectory(
  options: ResolveHelperRendererBundleDirectoryOptions = {},
): Promise<string> {
  const configured =
    "configuredDirectory" in options
      ? options.configuredDirectory
      : process.env.GOAL_PROGRESS_RENDERER_BUNDLE_DIR;
  if (configured) {
    return resolve(configured);
  }
  const executablePath = "executablePath" in options ? options.executablePath : process.execPath;
  const moduleUrl =
    "moduleUrl" in options
      ? options.moduleUrl
      : typeof import.meta.url === "string"
        ? import.meta.url
        : undefined;
  const candidates = executablePath ? [resolve(dirname(executablePath), "../renderer")] : [];
  if (moduleUrl) {
    candidates.push(
      fileURLToPath(new URL("../../../renderer/", moduleUrl)),
      fileURLToPath(new URL("../../../dist/renderer/", moduleUrl)),
    );
  }
  for (const candidate of candidates) {
    try {
      await readFile(resolve(candidate, "goal-progress.manifest.json"));
      return candidate;
    } catch {
      // Try the source-tree or built-tree location next.
    }
  }
  throw new Error("GOAL_PROGRESS_RENDERER_BUNDLE_NOT_FOUND");
}

export async function connectHelperRendererBridge(
  paths: GoalProgressPaths,
): Promise<GoalProgressRendererBridge | undefined> {
  if (process.platform !== "darwin") {
    return undefined;
  }
  const statePath = resolve(paths.runtimeRoot, "cdp.json");
  let state: Awaited<ReturnType<typeof readCodexCdpRuntimeState>>;
  try {
    state = await readCodexCdpRuntimeState(statePath);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return undefined;
    }
    throw error;
  }
  const app = await inspectCodexMacosApp(state.appPath);
  if (
    app.realExecutablePath !== state.executablePath ||
    app.bundleId !== state.bundleId ||
    app.teamId !== state.teamId
  ) {
    throw new Error("GOAL_PROGRESS_CDP_RUNTIME_APP_MISMATCH");
  }
  const ownership = await verifyCodexCdpListenerOwnership(app, state.mainPid, state.port);
  if (
    ownership.mainProcess.startedAt !== state.processStartedAt ||
    ownership.mainProcess.command !== state.command
  ) {
    throw new Error("GOAL_PROGRESS_CDP_RUNTIME_OWNERSHIP_CHANGED");
  }
  const bundleDirectory = await resolveHelperRendererBundleDirectory();
  const [source, manifestText] = await Promise.all([
    readFile(resolve(bundleDirectory, "goal-progress.js"), "utf8"),
    readFile(resolve(bundleDirectory, "goal-progress.manifest.json"), "utf8"),
  ]);
  const bundle = createGoalProgressRendererBundle(source, JSON.parse(manifestText));
  const viewClient = new GoalProgressCdpViewClient(paths.helperSocketPath);
  let targetId: string | undefined;
  const connected = await connectGoalProgressRendererBridge({
    port: state.port,
    bundle,
    platform: "macos",
    appVersion: app.shortVersion,
    onUiIntent: (threadId, intent) => viewClient.applyUiIntent(threadId, intent),
    onUpdateIntent: (threadId, intent) => viewClient.applyUpdateIntent(threadId, intent),
    onVisibleThreadChange: (threadId, sequence, lifecycleId) =>
      targetId
        ? viewClient.reportVisibleThread(targetId, threadId, sequence, lifecycleId)
        : undefined,
    onDisconnected: (code) =>
      targetId ? viewClient.reportDisconnected(targetId, code) : undefined,
    environment: {
      appPath: app.realAppPath,
      appSignatureValid: app.signatureValid,
    },
  });
  targetId = connected.targetId;
  return connected.bridge;
}

export async function connectHelperRendererTargetSource(
  paths: GoalProgressPaths,
): Promise<RendererTargetSource | undefined> {
  if (process.platform !== "darwin") {
    return undefined;
  }
  const statePath = resolve(paths.runtimeRoot, "cdp.json");
  let state: Awaited<ReturnType<typeof readCodexCdpRuntimeState>>;
  try {
    state = await readCodexCdpRuntimeState(statePath);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return undefined;
    }
    throw error;
  }
  const app = await inspectCodexMacosApp(state.appPath);
  if (
    app.realExecutablePath !== state.executablePath ||
    app.bundleId !== state.bundleId ||
    app.teamId !== state.teamId
  ) {
    throw new Error("GOAL_PROGRESS_CDP_RUNTIME_APP_MISMATCH");
  }
  const ownership = await verifyCodexCdpListenerOwnership(app, state.mainPid, state.port);
  if (
    ownership.mainProcess.startedAt !== state.processStartedAt ||
    ownership.mainProcess.command !== state.command
  ) {
    throw new Error("GOAL_PROGRESS_CDP_RUNTIME_OWNERSHIP_CHANGED");
  }
  const bundleDirectory = await resolveHelperRendererBundleDirectory();
  const [source, manifestText, discovery] = await Promise.all([
    readFile(resolve(bundleDirectory, "goal-progress.js"), "utf8"),
    readFile(resolve(bundleDirectory, "goal-progress.manifest.json"), "utf8"),
    discoverCodexCdp(state.port),
  ]);
  const bundle = createGoalProgressRendererBundle(source, JSON.parse(manifestText));
  const viewClient = new GoalProgressCdpViewClient(paths.helperSocketPath);
  const browserClient = await CdpProtocolClient.connect(discovery.version.webSocketDebuggerUrl);
  const targetSource = createBrowserRendererTargetSource({
    port: state.port,
    browserClient,
    initialTargets: discovery.targets,
    connectTarget: async (target) =>
      (
        await connectGoalProgressRendererBridgeTarget(
          {
            port: state.port,
            bundle,
            platform: "macos",
            appVersion: app.shortVersion,
            onUiIntent: (threadId, intent) => viewClient.applyUiIntent(threadId, intent),
            onUpdateIntent: (threadId, intent) => viewClient.applyUpdateIntent(threadId, intent),
            onVisibleThreadChange: (threadId, sequence, lifecycleId) =>
              viewClient.reportVisibleThread(target.id, threadId, sequence, lifecycleId),
            onDisconnected: (code) => viewClient.reportDisconnected(target.id, code),
            environment: {
              appPath: app.realAppPath,
              appSignatureValid: app.signatureValid,
            },
          },
          target,
        )
      ).bridge,
  });
  try {
    await browserClient.send("Target.setDiscoverTargets", { discover: true });
  } catch (error) {
    await targetSource.close();
    throw error;
  }
  return targetSource;
}
