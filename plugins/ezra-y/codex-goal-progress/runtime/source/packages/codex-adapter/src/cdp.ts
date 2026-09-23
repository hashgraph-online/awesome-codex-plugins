import { z } from "zod";
import { GOAL_PROGRESS_RELEASE_VERSION } from "../../contracts/src/index.js";
import { resolveCurrentMacosVisibleThreadId } from "./anchor-adapter.js";
import { GOAL_PROGRESS_PAGE_HOST_VERSION } from "./page-host.js";
import {
  assertGoalProgressRendererBundle,
  type GoalProgressRendererBundle,
} from "./renderer-bundle.js";

const CDP_REQUEST_TIMEOUT_MS = 10_000;
const CDP_MAX_MESSAGE_BYTES = 4 * 1024 * 1024;
const CDP_MAX_HTTP_BYTES = 1024 * 1024;
export const CODEX_RENDERER_URL = "app://-/index.html";
const CODEX_LOCAL_THREAD_ROUTE_PATTERN = /^\/local\/[A-Za-z0-9][A-Za-z0-9_-]{0,255}$/u;

const CdpVersionSchema = z
  .object({
    Browser: z.string().min(1),
    "Protocol-Version": z.string().min(1),
    "User-Agent": z.string().min(1),
    webSocketDebuggerUrl: z.string().min(1),
  })
  .passthrough();

const CdpTargetSchema = z
  .object({
    id: z.string().regex(/^[A-Za-z0-9_-]+$/u),
    type: z.string().min(1),
    title: z.string(),
    url: z.string().min(1),
    webSocketDebuggerUrl: z.string().min(1),
  })
  .passthrough();

const CdpTargetTypeSchema = z
  .object({
    type: z.string(),
  })
  .passthrough();

const CdpResponseSchema = z
  .object({
    id: z.number().int().positive(),
    result: z.unknown().optional(),
    error: z
      .object({
        code: z.number(),
        message: z.string(),
      })
      .passthrough()
      .optional(),
  })
  .passthrough()
  .refine(
    (value) =>
      Object.hasOwn(value, "result") !== Object.hasOwn(value, "error") &&
      !Object.hasOwn(value, "method"),
  );

const CdpEventSchema = z
  .object({
    method: z.string().min(1),
    params: z.unknown().optional(),
  })
  .passthrough()
  .refine((value) => !Object.hasOwn(value, "id"));

export interface CodexCdpVersion {
  readonly browser: string;
  readonly protocolVersion: string;
  readonly userAgent: string;
  readonly webSocketDebuggerUrl: string;
}

export interface CodexCdpTarget {
  readonly id: string;
  readonly type: string;
  readonly title: string;
  readonly url: string;
  readonly webSocketDebuggerUrl: string;
}

export interface CodexCdpDiscovery {
  readonly version: CodexCdpVersion;
  readonly targets: readonly CodexCdpTarget[];
}

export function isCodexRendererPageUrl(rawUrl: string): boolean {
  let url: URL;
  try {
    url = new URL(rawUrl);
  } catch {
    return false;
  }
  if (
    url.protocol !== "app:" ||
    url.hostname !== "-" ||
    url.pathname !== "/index.html" ||
    url.username !== "" ||
    url.password !== "" ||
    url.hash !== ""
  ) {
    return false;
  }
  const keys = [...url.searchParams.keys()];
  if (keys.length === 0) {
    return url.search === "";
  }
  return (
    keys.length === 1 &&
    keys[0] === "initialRoute" &&
    CODEX_LOCAL_THREAD_ROUTE_PATTERN.test(url.searchParams.get("initialRoute") ?? "")
  );
}

export type FetchLike = (
  input: string | URL | globalThis.Request,
  init?: RequestInit,
) => Promise<Response>;

export type WebSocketFactory = (url: string) => WebSocket;

export interface CdpProtocolClientOptions {
  readonly requestTimeoutMs?: number;
  readonly webSocketFactory?: WebSocketFactory;
}

interface PendingCdpRequest {
  readonly method: string;
  readonly resolve: (result: unknown) => void;
  readonly reject: (error: Error) => void;
  readonly timeout: NodeJS.Timeout;
}

function cdpError(code: string, detail?: string): Error {
  return new Error(detail ? `${code}: ${detail}` : code);
}

function validateLoopbackWebSocketUrl(
  rawUrl: string,
  expectedPort: number,
  expectedPathPrefix: string,
): string {
  const url = new URL(rawUrl);
  if (
    url.protocol !== "ws:" ||
    url.hostname !== "127.0.0.1" ||
    Number(url.port) !== expectedPort ||
    url.username ||
    url.password ||
    !url.pathname.startsWith(expectedPathPrefix)
  ) {
    throw cdpError("GOAL_PROGRESS_CDP_UNSAFE_WEBSOCKET_URL", rawUrl);
  }
  return url.toString();
}

async function fetchJson(url: URL, fetchImpl: FetchLike): Promise<unknown> {
  const response = await fetchImpl(url, {
    method: "GET",
    redirect: "error",
    signal: AbortSignal.timeout(5_000),
  });
  if (!response.ok) {
    throw cdpError("GOAL_PROGRESS_CDP_HTTP_FAILED", `${response.status} ${url.pathname}`);
  }
  const text = await response.text();
  if (Buffer.byteLength(text) > CDP_MAX_HTTP_BYTES) {
    throw cdpError("GOAL_PROGRESS_CDP_HTTP_OUTPUT_LIMIT");
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    throw cdpError("GOAL_PROGRESS_CDP_HTTP_INVALID_JSON");
  }
}

export async function discoverCodexCdp(
  port: number,
  fetchImpl: FetchLike = fetch,
): Promise<CodexCdpDiscovery> {
  if (!Number.isInteger(port) || port < 1_024 || port > 65_535) {
    throw cdpError("GOAL_PROGRESS_CDP_INVALID_PORT", String(port));
  }
  const origin = new URL(`http://127.0.0.1:${port}`);
  const [rawVersion, rawTargets] = await Promise.all([
    fetchJson(new URL("/json/version", origin), fetchImpl),
    fetchJson(new URL("/json/list", origin), fetchImpl),
  ]);
  const version = CdpVersionSchema.parse(rawVersion);
  const browserWebSocketUrl = validateLoopbackWebSocketUrl(
    version.webSocketDebuggerUrl,
    port,
    "/devtools/browser/",
  );
  const targets = z
    .array(z.unknown())
    .parse(rawTargets)
    .flatMap((rawTarget) => {
      const candidate = CdpTargetTypeSchema.safeParse(rawTarget);
      if (!candidate.success || candidate.data.type !== "page") {
        return [];
      }
      const parsedTarget = CdpTargetSchema.safeParse(rawTarget);
      if (!parsedTarget.success) {
        return [];
      }
      const target = parsedTarget.data;
      let pageUrl: URL;
      try {
        pageUrl = new URL(target.url);
      } catch {
        return [];
      }
      if (target.type !== "page" || !isCodexRendererPageUrl(pageUrl.toString())) {
        return [];
      }
      const pageWebSocketUrl = validateLoopbackWebSocketUrl(
        target.webSocketDebuggerUrl,
        port,
        "/devtools/page/",
      );
      if (new URL(pageWebSocketUrl).pathname !== `/devtools/page/${target.id}`) {
        throw cdpError("GOAL_PROGRESS_CDP_TARGET_ID_MISMATCH", target.id);
      }
      return [
        {
          id: target.id,
          type: target.type,
          title: target.title,
          url: pageUrl.toString(),
          webSocketDebuggerUrl: pageWebSocketUrl,
        },
      ];
    });
  if (targets.length === 0) {
    throw cdpError("GOAL_PROGRESS_CDP_APP_RENDERER_NOT_FOUND");
  }
  return {
    version: {
      browser: version.Browser,
      protocolVersion: version["Protocol-Version"],
      userAgent: version["User-Agent"],
      webSocketDebuggerUrl: browserWebSocketUrl,
    },
    targets,
  };
}

export class CdpProtocolClient {
  readonly #socket: WebSocket;
  readonly #pending = new Map<number, PendingCdpRequest>();
  readonly #ignoredResponseIds = new Set<number>();
  readonly #requestTimeoutMs: number;
  readonly #eventMethods: string[] = [];
  readonly #eventListeners = new Map<string, Set<(params: unknown) => void>>();
  readonly #failureListeners = new Set<(error: Error) => void>();
  #nextId = 1;
  #closed = false;
  #failed: Error | undefined;

  private constructor(socket: WebSocket, requestTimeoutMs: number) {
    this.#socket = socket;
    this.#requestTimeoutMs = requestTimeoutMs;
    socket.addEventListener("message", (event) => {
      void this.#handleMessage(event.data);
    });
    socket.addEventListener("error", () => {
      this.#fail(cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_ERROR"));
    });
    socket.addEventListener("close", () => {
      if (!this.#closed) {
        this.#fail(cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_CLOSED"));
      }
    });
  }

  static async connect(
    url: string,
    options: CdpProtocolClientOptions = {},
  ): Promise<CdpProtocolClient> {
    const parsedUrl = new URL(url);
    if (parsedUrl.protocol !== "ws:" || parsedUrl.hostname !== "127.0.0.1") {
      throw cdpError("GOAL_PROGRESS_CDP_UNSAFE_WEBSOCKET_URL", url);
    }
    const factory = options.webSocketFactory ?? ((socketUrl) => new WebSocket(socketUrl));
    const socket = factory(parsedUrl.toString());
    await new Promise<void>((resolveOpen, rejectOpen) => {
      const timeout = setTimeout(() => {
        rejectOpen(cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_OPEN_TIMEOUT"));
      }, options.requestTimeoutMs ?? CDP_REQUEST_TIMEOUT_MS);
      socket.addEventListener(
        "open",
        () => {
          clearTimeout(timeout);
          resolveOpen();
        },
        { once: true },
      );
      socket.addEventListener(
        "error",
        () => {
          clearTimeout(timeout);
          rejectOpen(cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_OPEN_FAILED"));
        },
        { once: true },
      );
    });
    return new CdpProtocolClient(socket, options.requestTimeoutMs ?? CDP_REQUEST_TIMEOUT_MS);
  }

  get eventMethods(): readonly string[] {
    return [...this.#eventMethods];
  }

  onEvent(method: string, listener: (params: unknown) => void): () => void {
    const listeners = this.#eventListeners.get(method) ?? new Set();
    listeners.add(listener);
    this.#eventListeners.set(method, listeners);
    return () => {
      listeners.delete(listener);
      if (listeners.size === 0) {
        this.#eventListeners.delete(method);
      }
    };
  }

  onFailure(listener: (error: Error) => void): () => void {
    this.#failureListeners.add(listener);
    if (this.#failed) {
      try {
        listener(this.#failed);
      } catch {
        // Failure observers cannot change the existing transport failure.
      }
    }
    return () => {
      this.#failureListeners.delete(listener);
    };
  }

  async waitForEvent(
    method: string,
    afterIndex: number,
    timeoutMs = this.#requestTimeoutMs,
  ): Promise<void> {
    const timeoutAt = Date.now() + timeoutMs;
    do {
      this.assertHealthy();
      if (this.#eventMethods.slice(afterIndex).includes(method)) {
        return;
      }
      await new Promise((resolveDelay) => setTimeout(resolveDelay, 100));
    } while (Date.now() < timeoutAt);
    throw cdpError("GOAL_PROGRESS_CDP_EVENT_TIMEOUT", method);
  }

  async send(method: string, params: unknown = {}): Promise<unknown> {
    if (this.#closed || this.#failed) {
      throw this.#failed ?? cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_CLOSED");
    }
    const id = this.#nextId;
    this.#nextId += 1;
    const response = new Promise<unknown>((resolveResponse, rejectResponse) => {
      const timeout = setTimeout(() => {
        this.#pending.delete(id);
        rejectResponse(cdpError("GOAL_PROGRESS_CDP_REQUEST_TIMEOUT", method));
      }, this.#requestTimeoutMs);
      this.#pending.set(id, {
        method,
        resolve: resolveResponse,
        reject: rejectResponse,
        timeout,
      });
    });
    this.#socket.send(JSON.stringify({ id, method, params }));
    return response;
  }

  sendWithoutResponse(method: string, params: unknown = {}): void {
    if (this.#closed || this.#failed) {
      throw this.#failed ?? cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_CLOSED");
    }
    const id = this.#nextId;
    this.#nextId += 1;
    this.#ignoredResponseIds.add(id);
    this.#socket.send(JSON.stringify({ id, method, params }));
  }

  assertHealthy(): void {
    if (this.#failed) {
      throw this.#failed;
    }
  }

  async close(): Promise<void> {
    if (this.#closed) {
      return;
    }
    this.#closed = true;
    for (const pending of this.#pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(cdpError("GOAL_PROGRESS_CDP_WEBSOCKET_CLOSED"));
    }
    this.#pending.clear();
    this.#ignoredResponseIds.clear();
    if (this.#socket.readyState === WebSocket.CLOSED) {
      return;
    }
    await new Promise<void>((resolveClose) => {
      const timeout = setTimeout(resolveClose, 1_000);
      this.#socket.addEventListener(
        "close",
        () => {
          clearTimeout(timeout);
          resolveClose();
        },
        { once: true },
      );
      this.#socket.close();
    });
  }

  async #handleMessage(data: unknown): Promise<void> {
    let text: string;
    if (typeof data === "string") {
      text = data;
    } else if (data instanceof ArrayBuffer) {
      text = Buffer.from(data).toString("utf8");
    } else if (data instanceof Blob) {
      text = await data.text();
    } else {
      this.#fail(cdpError("GOAL_PROGRESS_CDP_INVALID_MESSAGE_TYPE"));
      return;
    }
    if (Buffer.byteLength(text) > CDP_MAX_MESSAGE_BYTES) {
      this.#fail(cdpError("GOAL_PROGRESS_CDP_MESSAGE_LIMIT"));
      return;
    }
    let value: unknown;
    try {
      value = JSON.parse(text) as unknown;
    } catch {
      this.#fail(cdpError("GOAL_PROGRESS_CDP_INVALID_JSON"));
      return;
    }
    const response = CdpResponseSchema.safeParse(value);
    if (response.success) {
      if (this.#ignoredResponseIds.delete(response.data.id)) {
        if (response.data.error) {
          this.#fail(
            cdpError(
              "GOAL_PROGRESS_CDP_REQUEST_FAILED",
              `unacknowledged command: ${response.data.error.message}`,
            ),
          );
        }
        return;
      }
      const pending = this.#pending.get(response.data.id);
      if (!pending) {
        this.#fail(cdpError("GOAL_PROGRESS_CDP_UNEXPECTED_RESPONSE"));
        return;
      }
      clearTimeout(pending.timeout);
      this.#pending.delete(response.data.id);
      if (response.data.error) {
        pending.reject(
          cdpError(
            "GOAL_PROGRESS_CDP_REQUEST_FAILED",
            `${pending.method}: ${response.data.error.message}`,
          ),
        );
      } else {
        pending.resolve(response.data.result);
      }
      return;
    }
    const event = CdpEventSchema.safeParse(value);
    if (event.success) {
      this.#eventMethods.push(event.data.method);
      for (const listener of this.#eventListeners.get(event.data.method) ?? []) {
        try {
          listener(event.data.params);
        } catch {
          // Event observers cannot break the CDP transport.
        }
      }
      return;
    }
    this.#fail(cdpError("GOAL_PROGRESS_CDP_UNEXPECTED_MESSAGE"));
  }

  #fail(error: Error): void {
    if (this.#failed) {
      return;
    }
    this.#failed = error;
    for (const pending of this.#pending.values()) {
      clearTimeout(pending.timeout);
      pending.reject(error);
    }
    this.#pending.clear();
    this.#ignoredResponseIds.clear();
    for (const listener of this.#failureListeners) {
      try {
        listener(error);
      } catch {
        // Failure observers cannot break transport cleanup.
      }
    }
    this.#socket.close();
  }
}

export interface CdpCommandSender {
  send(method: string, params?: unknown): Promise<unknown>;
}

export type GoalProgressPageApiMethod =
  | "mount"
  | "update"
  | "setUpdateState"
  | "unmount"
  | "health";

const goalProgressPageApiFunctions: Readonly<Record<GoalProgressPageApiMethod, string>> = {
  mount: "function(input) { return this.mount(input); }",
  update: "function(input) { return this.update(input); }",
  setUpdateState: "function(input) { return this.setUpdateState(input); }",
  unmount: "function() { return this.unmount(); }",
  health: "function() { return this.health(); }",
};

const RuntimeObjectHandleSchema = z
  .object({
    result: z
      .object({
        type: z.string(),
        objectId: z.string().min(1),
      })
      .passthrough(),
    exceptionDetails: z.never().optional(),
  })
  .passthrough();

const RuntimeCallByValueResultSchema = z
  .object({
    result: z
      .object({
        value: z.unknown(),
      })
      .passthrough(),
    exceptionDetails: z.never().optional(),
  })
  .passthrough();

const GoalProgressBundleInstalledSchema = z
  .object({
    result: z
      .object({
        value: z.literal(true),
      })
      .passthrough(),
    exceptionDetails: z.never().optional(),
  })
  .passthrough();

const GoalProgressNewDocumentScriptSchema = z
  .object({
    identifier: z.string().min(1),
  })
  .passthrough();

export interface GoalProgressPageBundleInstallResult {
  readonly installed: true;
  readonly newDocumentScriptIdentifier: string;
}

export async function installGoalProgressPageBundle(
  sender: CdpCommandSender,
  bundleInput: GoalProgressRendererBundle,
): Promise<GoalProgressPageBundleInstallResult> {
  const bundle = assertGoalProgressRendererBundle(bundleInput);
  await sender.send("Page.enable");
  await sender.send("Runtime.enable");
  const newDocumentScript = GoalProgressNewDocumentScriptSchema.parse(
    await sender.send("Page.addScriptToEvaluateOnNewDocument", {
      source: bundle.source,
    }),
  );
  try {
    await evaluateGoalProgressPageBundle(sender, bundle);
  } catch (error) {
    await sender.send("Page.removeScriptToEvaluateOnNewDocument", {
      identifier: newDocumentScript.identifier,
    });
    throw error;
  }
  return {
    installed: true,
    newDocumentScriptIdentifier: newDocumentScript.identifier,
  };
}

export async function evaluateGoalProgressPageBundle(
  sender: CdpCommandSender,
  bundleInput: GoalProgressRendererBundle,
): Promise<void> {
  const bundle = assertGoalProgressRendererBundle(bundleInput);
  await sender.send("Runtime.evaluate", {
    expression: bundle.source,
    awaitPromise: true,
    returnByValue: true,
  });
  GoalProgressBundleInstalledSchema.parse(
    await sender.send("Runtime.evaluate", {
      expression: `globalThis.__CODEX_GOAL_PROGRESS__?.version === ${GOAL_PROGRESS_PAGE_HOST_VERSION} && globalThis.__CODEX_GOAL_PROGRESS__?.releaseVersion === ${JSON.stringify(GOAL_PROGRESS_RELEASE_VERSION)}`,
      awaitPromise: true,
      returnByValue: true,
    }),
  );
}

export async function invokeGoalProgressPageApi(
  sender: CdpCommandSender,
  method: GoalProgressPageApiMethod,
  argument?: unknown,
): Promise<unknown> {
  const handle = RuntimeObjectHandleSchema.parse(
    await sender.send("Runtime.evaluate", {
      expression: "globalThis.__CODEX_GOAL_PROGRESS__",
      objectGroup: "codex-goal-progress",
      returnByValue: false,
      awaitPromise: true,
    }),
  );
  try {
    const parameters = {
      objectId: handle.result.objectId,
      functionDeclaration: goalProgressPageApiFunctions[method],
      awaitPromise: true,
      returnByValue: true,
      ...(argument === undefined ? {} : { arguments: [{ value: argument }] }),
    };
    return RuntimeCallByValueResultSchema.parse(
      await sender.send("Runtime.callFunctionOn", parameters),
    ).result.value;
  } finally {
    await sender.send("Runtime.releaseObject", {
      objectId: handle.result.objectId,
    });
  }
}

const VisibleGoalProgressThreadResultSchema = z
  .object({
    result: z
      .object({
        value: z.string().trim().min(1).max(256).nullable(),
      })
      .passthrough(),
  })
  .passthrough();

const visibleGoalProgressThreadExpression = `(${resolveCurrentMacosVisibleThreadId.toString()})(document)`;

const GOAL_PROGRESS_VISIBLE_THREAD_WATCHER_KEY = "__CODEX_GOAL_PROGRESS_VISIBLE_THREAD_WATCHER__";

export function createGoalProgressVisibleThreadWatcherSource(
  bindingName: string,
  bridgeNonce: string,
  watcherId: string = bridgeNonce,
): string {
  if (
    !/^__CODEX_GOAL_PROGRESS_VISIBLE_THREAD_[A-Za-z0-9_-]{32}$/u.test(bindingName) ||
    !/^[A-Za-z0-9_-]{32}$/u.test(bridgeNonce) ||
    !/^[A-Za-z0-9_-]{32}$/u.test(watcherId)
  ) {
    throw cdpError("GOAL_PROGRESS_VISIBLE_THREAD_WATCHER_IDENTITY_INVALID");
  }
  return `(() => {
    const key = ${JSON.stringify(GOAL_PROGRESS_VISIBLE_THREAD_WATCHER_KEY)};
    const previous = globalThis[key];
    if (previous && typeof previous.disconnect === "function") {
      previous.disconnect();
    }
    const bindingName = ${JSON.stringify(bindingName)};
    const bridgeNonce = ${JSON.stringify(bridgeNonce)};
    const watcherId = ${JSON.stringify(watcherId)};
    const readVisibleThreadId = ${resolveCurrentMacosVisibleThreadId.toString()};
    let initialized = false;
    let lastThreadId = null;
    let sequence = 0;
    let scheduled = false;
    const report = () => {
      scheduled = false;
      const threadId = readVisibleThreadId(document);
      if (initialized && threadId === lastThreadId) {
        return;
      }
      initialized = true;
      lastThreadId = threadId;
      sequence += 1;
      const binding = globalThis[bindingName];
      if (typeof binding === "function") {
        binding(JSON.stringify({
          protocolVersion: 1,
          bridgeNonce,
          lifecycleId: watcherId,
          type: "visibleThreadChanged",
          threadId,
          sequence
        }));
      }
    };
    const relevant = (record) => {
      const target = record.target;
      if (target instanceof Element && target.closest("[data-app-action-sidebar-thread-row]")) {
        return true;
      }
      if (
        target instanceof Element &&
        target.matches("[data-response-annotation-conversation]")
      ) {
        return true;
      }
      return Array.from(record.addedNodes || []).some(
        (node) =>
          node instanceof Element &&
          (node.matches("[data-app-action-sidebar-thread-row]") ||
            node.querySelector("[data-app-action-sidebar-thread-row]") ||
            node.matches("[data-response-annotation-conversation]") ||
            node.querySelector("[data-response-annotation-conversation]"))
      );
    };
    let observer = null;
    const start = () => {
      if (observer || !document.documentElement) {
        return;
      }
      observer = new MutationObserver((records) => {
        if (!records.some(relevant) || scheduled) {
          return;
        }
        scheduled = true;
        queueMicrotask(report);
      });
      observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: [
          "aria-current",
          "data-app-action-sidebar-thread-active",
          "data-app-action-sidebar-thread-host-id",
          "data-app-action-sidebar-thread-id",
          "data-app-action-sidebar-thread-selected",
          "data-response-annotation-conversation"
        ],
        childList: true,
        subtree: true
      });
      report();
    };
    const onReady = () => start();
    Object.defineProperty(globalThis, key, {
      configurable: true,
      value: Object.freeze({
        disconnect() {
          removeEventListener("DOMContentLoaded", onReady);
          observer?.disconnect();
        }
      })
    });
    if (document.documentElement) {
      start();
    } else {
      addEventListener("DOMContentLoaded", onReady, { once: true });
    }
  })();`;
}

export async function installGoalProgressVisibleThreadWatcher(
  sender: CdpCommandSender,
  bindingName: string,
  bridgeNonce: string,
  watcherId: string = bridgeNonce,
): Promise<void> {
  const source = createGoalProgressVisibleThreadWatcherSource(bindingName, bridgeNonce, watcherId);
  await sender.send("Page.enable");
  await sender.send("Runtime.enable");
  await sender.send("Page.addScriptToEvaluateOnNewDocument", { source });
  await refreshGoalProgressVisibleThreadWatcher(sender, bindingName, bridgeNonce, watcherId);
}

export async function refreshGoalProgressVisibleThreadWatcher(
  sender: CdpCommandSender,
  bindingName: string,
  bridgeNonce: string,
  watcherId: string = bridgeNonce,
): Promise<void> {
  const source = createGoalProgressVisibleThreadWatcherSource(bindingName, bridgeNonce, watcherId);
  await sender.send("Runtime.addBinding", { name: bindingName });
  await sender.send("Runtime.evaluate", {
    expression: source,
    awaitPromise: true,
    returnByValue: true,
  });
}

export async function readGoalProgressVisibleThreadId(
  sender: CdpCommandSender,
): Promise<string | undefined> {
  const response = VisibleGoalProgressThreadResultSchema.parse(
    await sender.send("Runtime.evaluate", {
      expression: visibleGoalProgressThreadExpression,
      returnByValue: true,
      awaitPromise: true,
    }),
  );
  return response.result.value ?? undefined;
}

const markerExpression = `(() => {
  Object.defineProperty(globalThis, "__CODEX_GOAL_PROGRESS_CDP_POC__", {
    configurable: true,
    value: Object.freeze({ version: 1 })
  });
  return globalThis.__CODEX_GOAL_PROGRESS_CDP_POC__.version === 1;
})()`;

const markerCheckExpression = "globalThis.__CODEX_GOAL_PROGRESS_CDP_POC__?.version === 1";
const documentSentinelExpression = "globalThis.__CODEX_GOAL_PROGRESS_DOCUMENT_SENTINEL__ = true";
const reloadStateExpression = `({
  sentinelPresent: globalThis.__CODEX_GOAL_PROGRESS_DOCUMENT_SENTINEL__ === true,
  markerVisible: globalThis.__CODEX_GOAL_PROGRESS_CDP_POC__?.version === 1
})`;

const RuntimeEvaluateResultSchema = z
  .object({
    result: z
      .object({
        value: z.unknown().optional(),
      })
      .passthrough(),
  })
  .passthrough();

const NewDocumentScriptResultSchema = z
  .object({
    identifier: z.string().min(1),
  })
  .passthrough();

const ReloadStateSchema = z.object({
  sentinelPresent: z.boolean(),
  markerVisible: z.boolean(),
});

async function evaluateBoolean(client: CdpProtocolClient, expression: string): Promise<boolean> {
  return (await evaluateValue(client, expression)) === true;
}

async function evaluateValue(client: CdpProtocolClient, expression: string): Promise<unknown> {
  const result = RuntimeEvaluateResultSchema.parse(
    await client.send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    }),
  );
  return result.result.value;
}

async function waitForDocumentReady(client: CdpProtocolClient): Promise<void> {
  const timeoutAt = Date.now() + 15_000;
  do {
    if ((await evaluateValue(client, "document.readyState")) === "complete") {
      await new Promise((resolveDelay) => setTimeout(resolveDelay, 500));
      return;
    }
    await new Promise((resolveDelay) => setTimeout(resolveDelay, 250));
  } while (Date.now() < timeoutAt);
  throw cdpError("GOAL_PROGRESS_CDP_DOCUMENT_READY_TIMEOUT");
}

export interface CdpMarkerProbeResult {
  readonly initialMarkerVisible: boolean;
  readonly documentChangedAfterReload: boolean;
  readonly newDocumentScriptAppliedAfterReload: boolean;
  readonly hostReinjectedAfterReload: boolean;
  readonly markerVisibleAfterReload: boolean;
  readonly newDocumentScriptIdentifier: string;
  readonly eventMethods: readonly string[];
}

export interface CdpMarkerProbeOptions extends CdpProtocolClientOptions {
  readonly pageUrl: string;
}

export async function exerciseCodexCdpMarker(
  webSocketDebuggerUrl: string,
  options: CdpMarkerProbeOptions,
): Promise<CdpMarkerProbeResult> {
  const pageUrl = new URL(options.pageUrl);
  if (pageUrl.toString() !== CODEX_RENDERER_URL) {
    throw cdpError("GOAL_PROGRESS_CDP_UNSAFE_PAGE_URL", options.pageUrl);
  }
  const client = await CdpProtocolClient.connect(webSocketDebuggerUrl, options);
  try {
    await client.send("Page.enable");
    await client.send("Runtime.enable");
    await waitForDocumentReady(client);
    const newDocumentScript = NewDocumentScriptResultSchema.parse(
      await client.send("Page.addScriptToEvaluateOnNewDocument", {
        source: markerExpression,
      }),
    );
    const initialMarkerVisible = await evaluateBoolean(client, markerExpression);
    await evaluateBoolean(client, documentSentinelExpression);
    const eventCursor = client.eventMethods.length;
    client.sendWithoutResponse("Page.navigate", {
      url: pageUrl.toString(),
    });
    await client.waitForEvent("Page.loadEventFired", eventCursor, 15_000);
    const reloadState = ReloadStateSchema.parse(await evaluateValue(client, reloadStateExpression));
    const documentChangedAfterReload = !reloadState.sentinelPresent;
    const newDocumentScriptAppliedAfterReload =
      documentChangedAfterReload && reloadState.markerVisible;

    let hostReinjectedAfterReload = false;
    if (documentChangedAfterReload && !newDocumentScriptAppliedAfterReload) {
      hostReinjectedAfterReload = await evaluateBoolean(client, markerExpression);
    }
    const markerVisibleAfterReload =
      documentChangedAfterReload && (await evaluateBoolean(client, markerCheckExpression));
    client.assertHealthy();

    await client.send("Runtime.evaluate", {
      expression:
        "delete globalThis.__CODEX_GOAL_PROGRESS_CDP_POC__; delete globalThis.__CODEX_GOAL_PROGRESS_DOCUMENT_SENTINEL__",
      returnByValue: true,
    });
    return {
      initialMarkerVisible,
      documentChangedAfterReload,
      newDocumentScriptAppliedAfterReload,
      hostReinjectedAfterReload,
      markerVisibleAfterReload,
      newDocumentScriptIdentifier: newDocumentScript.identifier,
      eventMethods: client.eventMethods,
    };
  } finally {
    await client.close();
  }
}
