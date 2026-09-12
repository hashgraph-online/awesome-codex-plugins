import { type ChildProcessWithoutNullStreams, spawn } from "node:child_process";
import { createInterface } from "node:readline";
import { z } from "zod";
import {
  GOAL_PROGRESS_RELEASE_VERSION,
  type NativeGoalTokenUsage,
  type ThreadGoal,
  ThreadGoalGetResponseSchema,
  type ThreadTokenUsageUpdatedNotification,
  ThreadTokenUsageUpdatedNotificationSchema,
} from "../../contracts/src/index.js";
import type { ThreadCatalog, ThreadCatalogEntry } from "./thread-resolver.js";

export * from "./anchor-adapter.js";
export * from "./app-server-runtime.js";
export * from "./cdp.js";
export * from "./page-host.js";
export * from "./renderer-bridge.js";
export * from "./renderer-bundle.js";
export * from "./sidecar-mount.js";
export * from "./thread-resolver.js";
export * from "./ui-intent-bridge.js";
export * from "./view-client.js";

const APP_SERVER_REQUEST_TIMEOUT_MS = 10_000;
const APP_SERVER_MAX_OUTPUT_BYTES = 4 * 1024 * 1024;

const RequestIdSchema = z.union([z.string(), z.number()]);

const RpcResultResponseSchema = z
  .object({
    id: RequestIdSchema,
    result: z.unknown(),
  })
  .passthrough()
  .refine(
    (value) =>
      Object.hasOwn(value, "result") &&
      !Object.hasOwn(value, "error") &&
      !Object.hasOwn(value, "method"),
  );

const RpcErrorResponseSchema = z
  .object({
    id: RequestIdSchema,
    error: z
      .object({
        code: z.number().optional(),
        message: z.string(),
      })
      .passthrough(),
  })
  .passthrough()
  .refine(
    (value) =>
      Object.hasOwn(value, "error") &&
      !Object.hasOwn(value, "result") &&
      !Object.hasOwn(value, "method"),
  );

const RpcResponseSchema = z.union([RpcResultResponseSchema, RpcErrorResponseSchema]);

const ServerRequestSchema = z
  .object({
    id: RequestIdSchema,
    method: z.string().min(1),
  })
  .passthrough();

const NotificationSchema = z
  .object({
    method: z.string().min(1),
    params: z.unknown().optional(),
  })
  .passthrough()
  .refine((value) => !Object.hasOwn(value, "id"));

const TurnListResponseSchema = z
  .object({
    data: z.array(
      z
        .object({
          id: z.string().min(1),
        })
        .passthrough(),
    ),
  })
  .passthrough();

const ThreadListItemSchema = z
  .object({
    id: z.string().min(1).optional(),
    threadId: z.string().min(1).optional(),
    cwd: z.string().min(1).optional(),
    recencyAt: z.number().optional(),
    updatedAt: z.number().optional(),
  })
  .passthrough();

const ThreadListResponseSchema = z
  .object({
    data: z.array(ThreadListItemSchema),
  })
  .passthrough();

const ThreadIdentitySchema = z
  .object({
    id: z.string().min(1),
    sessionId: z.string().min(1),
    cwd: z.string().min(1),
    threadSource: z.string().min(1).nullable(),
    agentRole: z.string().min(1).nullable(),
    ephemeral: z.boolean(),
    status: z
      .object({
        type: z.string().min(1),
      })
      .passthrough(),
  })
  .passthrough();

const ThreadReadResponseSchema = z
  .object({
    thread: ThreadIdentitySchema,
  })
  .passthrough();

export type CodexThreadIdentity = z.infer<typeof ThreadIdentitySchema>;

interface PendingRequest {
  readonly method: string;
  readonly resolve: (value: unknown) => void;
  readonly reject: (error: Error) => void;
  readonly timeout: NodeJS.Timeout;
}

export interface CodexAppServerClientOptions {
  readonly command?: string;
  readonly args?: readonly string[];
  readonly cwd?: string;
  readonly env?: NodeJS.ProcessEnv;
  readonly requestTimeoutMs?: number;
  readonly onNotification?: (notification: AppServerNotificationSummary) => void;
}

export interface AppServerNotificationSummary {
  readonly method: string;
  readonly threadId?: string;
  readonly tokenUsage?: ThreadTokenUsageUpdatedNotification;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function threadCatalogEntry(
  item: z.infer<typeof ThreadListItemSchema>,
): ThreadCatalogEntry | undefined {
  const threadId = item.threadId ?? item.id;
  if (!threadId) {
    return undefined;
  }
  const recencyAt = item.recencyAt ?? item.updatedAt;
  return {
    threadId,
    ...(item.cwd === undefined ? {} : { cwd: item.cwd }),
    ...(recencyAt === undefined ? {} : { recencyAt }),
  };
}

export class CodexAppServerClient implements ThreadCatalog {
  readonly #child: ChildProcessWithoutNullStreams;
  readonly #pending = new Map<string | number, PendingRequest>();
  readonly #requestTimeoutMs: number;
  readonly #requestMethods: string[] = [];
  readonly #notifications: AppServerNotificationSummary[] = [];
  readonly #tokenUsageNotifications: ThreadTokenUsageUpdatedNotification[] = [];
  readonly #closed: Promise<void>;
  readonly #onNotification: ((notification: AppServerNotificationSummary) => void) | undefined;
  #resolveClosed!: () => void;
  #nextRequestId = 1;
  #outputBytes = 0;
  #stderr = "";
  #failed: Error | undefined;
  #closing = false;
  #forcedTermination = false;

  private constructor(options: CodexAppServerClientOptions) {
    this.#requestTimeoutMs = options.requestTimeoutMs ?? APP_SERVER_REQUEST_TIMEOUT_MS;
    this.#onNotification = options.onNotification;
    this.#closed = new Promise((resolveClosed) => {
      this.#resolveClosed = resolveClosed;
    });
    this.#child = spawn(options.command ?? "codex", options.args ?? ["app-server", "--stdio"], {
      cwd: options.cwd,
      env: options.env ?? process.env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    this.#child.stdout.setEncoding("utf8");
    this.#child.stderr.setEncoding("utf8");
    const lines = createInterface({ input: this.#child.stdout });
    lines.on("line", (line) => {
      this.#outputBytes += Buffer.byteLength(line) + 1;
      if (this.#outputBytes > APP_SERVER_MAX_OUTPUT_BYTES) {
        this.#fail(new Error("GOAL_PROGRESS_APP_SERVER_OUTPUT_LIMIT"));
        return;
      }
      this.#handleLine(line);
    });
    this.#child.stderr.on("data", (chunk: string) => {
      this.#stderr = `${this.#stderr}${chunk}`.slice(-8_000);
    });
    this.#child.on("error", (error) => {
      this.#fail(error);
    });
    this.#child.on("close", (code) => {
      if (!this.#closing && !this.#failed) {
        this.#fail(
          new Error(`GOAL_PROGRESS_APP_SERVER_EXITED: code=${String(code)} stderr=${this.#stderr}`),
        );
      }
      this.#resolveClosed();
    });
  }

  static async connect(options: CodexAppServerClientOptions = {}): Promise<CodexAppServerClient> {
    const client = new CodexAppServerClient(options);
    try {
      await client.#request("initialize", {
        clientInfo: {
          name: "codex-goal-progress",
          title: "Codex Goal Progress",
          version: GOAL_PROGRESS_RELEASE_VERSION,
        },
        capabilities: {
          experimentalApi: true,
          requestAttestation: false,
        },
      });
      client.#write({ method: "initialized" });
      return client;
    } catch (error) {
      await client.close();
      throw error;
    }
  }

  get closed(): Promise<void> {
    return this.#closed;
  }

  get failed(): Error | undefined {
    return this.#failed;
  }

  get requestMethods(): readonly string[] {
    return [...this.#requestMethods];
  }

  get notificationMethods(): readonly string[] {
    return this.#notifications.map((notification) => notification.method);
  }

  get notifications(): readonly AppServerNotificationSummary[] {
    return [...this.#notifications];
  }

  get tokenUsageNotifications(): readonly ThreadTokenUsageUpdatedNotification[] {
    return [...this.#tokenUsageNotifications];
  }

  async getGoal(threadId: string): Promise<ThreadGoal | null> {
    const result = await this.#request("thread/goal/get", { threadId });
    return ThreadGoalGetResponseSchema.parse(result).goal;
  }

  async readThreadIdentity(threadId: string): Promise<CodexThreadIdentity> {
    const result = await this.#request("thread/read", {
      threadId,
      includeTurns: false,
    });
    return ThreadReadResponseSchema.parse(result).thread;
  }

  async listTurnIds(threadId: string): Promise<readonly string[]> {
    const result = await this.#request("thread/turns/list", {
      threadId,
      limit: 100,
      sortDirection: "desc",
      itemsView: "summary",
    });
    return TurnListResponseSchema.parse(result).data.map((turn) => turn.id);
  }

  async listLoadedThreads(): Promise<readonly ThreadCatalogEntry[]> {
    const result = await this.#request("thread/loaded/list", {});
    return ThreadListResponseSchema.parse(result).data.flatMap((item) => {
      const entry = threadCatalogEntry(item);
      return entry ? [entry] : [];
    });
  }

  async listThreads(
    filter: { readonly cwd?: string } = {},
  ): Promise<readonly ThreadCatalogEntry[]> {
    const result = await this.#request(
      "thread/list",
      filter.cwd === undefined ? {} : { cwd: filter.cwd },
    );
    return ThreadListResponseSchema.parse(result).data.flatMap((item) => {
      const entry = threadCatalogEntry(item);
      return entry ? [entry] : [];
    });
  }

  async settle(milliseconds: number): Promise<void> {
    await new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));
  }

  async close(): Promise<void> {
    if (this.#child.exitCode !== null) {
      await this.#closed;
      return;
    }
    this.#closing = true;
    this.#child.stdin.end();
    const closedGracefully = await Promise.race([
      this.#closed.then(() => true),
      new Promise<false>((resolveDelay) => setTimeout(() => resolveDelay(false), 1_000)),
    ]);
    if (closedGracefully) {
      return;
    }
    this.#forcedTermination = true;
    this.#child.kill("SIGTERM");
    const terminated = await Promise.race([
      this.#closed.then(() => true),
      new Promise<false>((resolveDelay) => setTimeout(() => resolveDelay(false), 1_000)),
    ]);
    if (!terminated) {
      this.#child.kill("SIGKILL");
      await this.#closed;
    }
  }

  async closeAndDrain(): Promise<void> {
    await this.close();
    if (this.#failed) {
      throw this.#failed;
    }
    if (this.#forcedTermination) {
      throw new Error("GOAL_PROGRESS_APP_SERVER_DRAIN_TIMEOUT");
    }
  }

  async #request(method: string, params: unknown): Promise<unknown> {
    if (this.#failed || this.#closing) {
      throw this.#failed ?? new Error("GOAL_PROGRESS_APP_SERVER_CLOSING");
    }
    const id = this.#nextRequestId;
    this.#nextRequestId += 1;
    this.#requestMethods.push(method);

    const response = new Promise<unknown>((resolveResponse, rejectResponse) => {
      const timeout = setTimeout(() => {
        this.#pending.delete(id);
        rejectResponse(new Error(`GOAL_PROGRESS_APP_SERVER_TIMEOUT: ${method}`));
      }, this.#requestTimeoutMs);
      this.#pending.set(id, {
        method,
        resolve: resolveResponse,
        reject: rejectResponse,
        timeout,
      });
    });
    try {
      this.#write({ id, method, params });
    } catch (error) {
      const pending = this.#pending.get(id);
      if (pending) {
        clearTimeout(pending.timeout);
        this.#pending.delete(id);
      }
      throw error;
    }
    return response;
  }

  #write(message: unknown): void {
    if (this.#failed || !this.#child.stdin.writable) {
      throw this.#failed ?? new Error("GOAL_PROGRESS_APP_SERVER_STDIN_CLOSED");
    }
    this.#child.stdin.write(`${JSON.stringify(message)}\n`);
  }

  #handleLine(line: string): void {
    let value: unknown;
    try {
      value = JSON.parse(line) as unknown;
    } catch {
      this.#fail(new Error("GOAL_PROGRESS_APP_SERVER_INVALID_JSON"));
      return;
    }

    const response = RpcResponseSchema.safeParse(value);
    if (response.success && this.#pending.has(response.data.id)) {
      const pending = this.#pending.get(response.data.id);
      if (!pending) {
        return;
      }
      clearTimeout(pending.timeout);
      this.#pending.delete(response.data.id);
      const errorResponse = RpcErrorResponseSchema.safeParse(response.data);
      if (errorResponse.success) {
        pending.reject(
          new Error(
            `GOAL_PROGRESS_APP_SERVER_REQUEST_FAILED: ${pending.method}: ${errorResponse.data.error.message}`,
          ),
        );
      } else {
        pending.resolve(RpcResultResponseSchema.parse(response.data).result);
      }
      return;
    }

    const serverRequest = ServerRequestSchema.safeParse(value);
    if (serverRequest.success) {
      this.#fail(
        new Error(`GOAL_PROGRESS_APP_SERVER_UNEXPECTED_REQUEST: ${serverRequest.data.method}`),
      );
      return;
    }

    const notification = NotificationSchema.safeParse(value);
    if (notification.success) {
      const params =
        notification.data.params !== null &&
        typeof notification.data.params === "object" &&
        !Array.isArray(notification.data.params)
          ? (notification.data.params as Record<string, unknown>)
          : undefined;
      const nestedThread =
        params?.thread !== null &&
        typeof params?.thread === "object" &&
        !Array.isArray(params.thread)
          ? (params.thread as Record<string, unknown>)
          : undefined;
      const threadId =
        typeof params?.threadId === "string"
          ? params.threadId
          : typeof nestedThread?.id === "string"
            ? nestedThread.id
            : undefined;
      let tokenUsage: ThreadTokenUsageUpdatedNotification | undefined;
      if (notification.data.method === "thread/tokenUsage/updated") {
        const parsedTokenUsage = ThreadTokenUsageUpdatedNotificationSchema.safeParse(
          notification.data.params,
        );
        if (!parsedTokenUsage.success) {
          this.#fail(new Error("GOAL_PROGRESS_APP_SERVER_INVALID_TOKEN_USAGE_NOTIFICATION"));
          return;
        }
        tokenUsage = parsedTokenUsage.data;
        this.#tokenUsageNotifications.push(tokenUsage);
      }
      const summary: AppServerNotificationSummary = {
        method: notification.data.method,
        ...(threadId === undefined ? {} : { threadId }),
        ...(tokenUsage === undefined ? {} : { tokenUsage }),
      };
      this.#notifications.push(summary);
      this.#onNotification?.(summary);
      return;
    }

    this.#fail(new Error("GOAL_PROGRESS_APP_SERVER_UNEXPECTED_MESSAGE"));
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
    this.#child.kill("SIGTERM");
  }
}

export interface NativeGoalTokenReader {
  getGoal(threadId: string): Promise<ThreadGoal | null>;
}

export async function readNativeGoalTokenUsage(
  reader: NativeGoalTokenReader,
  threadId: string,
): Promise<NativeGoalTokenUsage> {
  const expectedThreadId = z.string().trim().min(1).parse(threadId);
  let goal: ThreadGoal | null;
  try {
    goal = await reader.getGoal(expectedThreadId);
  } catch {
    return {
      schemaVersion: 1,
      availability: "unavailable",
      source: "unavailable",
      threadId: expectedThreadId,
      reason: "read-failed",
    };
  }
  if (!goal) {
    return {
      schemaVersion: 1,
      availability: "unavailable",
      source: "unavailable",
      threadId: expectedThreadId,
      reason: "goal-not-found",
    };
  }
  if (goal.threadId !== expectedThreadId) {
    return {
      schemaVersion: 1,
      availability: "unavailable",
      source: "unavailable",
      threadId: expectedThreadId,
      reason: "thread-mismatch",
    };
  }
  return {
    schemaVersion: 1,
    availability: "available",
    source: "native-goal",
    threadId: expectedThreadId,
    tokensUsed: goal.tokensUsed,
    tokenBudget: goal.tokenBudget ?? null,
    goalUpdatedAt: goal.updatedAt,
  };
}

export const NativeGoalProbeOperationSchema = z.enum(["get", "attach", "create"]);
export type NativeGoalProbeOperation = z.infer<typeof NativeGoalProbeOperationSchema>;

export interface NativeGoalProbeOptions extends CodexAppServerClientOptions {
  readonly operation: NativeGoalProbeOperation;
  readonly threadId: string;
  readonly objective?: string;
  readonly settleMs?: number;
}

export interface NativeGoalProbeResult {
  readonly schemaVersion: 1;
  readonly operation: NativeGoalProbeOperation;
  readonly outcome: "read" | "attached" | "created" | "conflict" | "unavailable";
  readonly passed: boolean;
  readonly mutationAttempted: boolean;
  readonly beforeGoal: ThreadGoal | null;
  readonly afterGoal: ThreadGoal | null;
  readonly beforeTurnIds: readonly string[];
  readonly afterTurnIds: readonly string[];
  readonly newTurnIds: readonly string[];
  readonly requestMethods: readonly string[];
  readonly notificationMethods: readonly string[];
  readonly notificationThreadIds: readonly string[];
  readonly assertions: {
    readonly sameThread: boolean;
    readonly objectivePreserved: boolean;
    readonly usageNotReset: boolean;
    readonly createdAtPreserved: boolean;
    readonly objectiveConflictProtected: boolean;
    readonly attachIsReadOnly: boolean;
    readonly notificationThreadsMatch: boolean;
    readonly noThreadStartOrFork: boolean;
    readonly noModelTurnStarted: boolean;
  };
  readonly errors: readonly string[];
}

const forbiddenControlMethods = new Set(["thread/start", "thread/fork", "turn/start"]);

export async function runNativeGoalProbe(
  options: NativeGoalProbeOptions,
): Promise<NativeGoalProbeResult> {
  const threadId = z.string().trim().min(1).parse(options.threadId);
  const operation = NativeGoalProbeOperationSchema.parse(options.operation);
  const client = await CodexAppServerClient.connect(options);

  try {
    const beforeGoal = await client.getGoal(threadId);
    const beforeTurnIds = await client.listTurnIds(threadId);
    const mutationAttempted = false;
    let outcome: NativeGoalProbeResult["outcome"] = "read";
    let objectiveConflictProtected = false;

    if (operation === "attach") {
      if (!beforeGoal) {
        outcome = "unavailable";
      } else if (options.objective && options.objective !== beforeGoal.objective) {
        outcome = "conflict";
        objectiveConflictProtected = true;
      } else {
        outcome = "attached";
      }
    } else if (operation === "create") {
      if (beforeGoal) {
        outcome = "conflict";
        objectiveConflictProtected = beforeGoal.objective !== options.objective;
      } else {
        outcome = "unavailable";
      }
    }

    await client.settle(options.settleMs ?? 1_000);
    const afterGoal = await client.getGoal(threadId);
    const afterTurnIds = await client.listTurnIds(threadId);
    await client.closeAndDrain();
    const beforeTurnSet = new Set(beforeTurnIds);
    const newTurnIds = afterTurnIds.filter((turnId) => !beforeTurnSet.has(turnId));
    const requestMethods = client.requestMethods;
    const notifications = client.notifications;
    const notificationMethods = notifications.map((notification) => notification.method);
    const notificationThreadIds = notifications.flatMap((notification) =>
      notification.threadId === undefined ? [] : [notification.threadId],
    );

    const sameThread =
      (beforeGoal === null || beforeGoal.threadId === threadId) &&
      (afterGoal === null || afterGoal.threadId === threadId);
    const objectivePreserved =
      operation !== "attach" ||
      !beforeGoal ||
      (afterGoal !== null && afterGoal.objective === beforeGoal.objective);
    const usageNotReset =
      operation !== "attach" ||
      !beforeGoal ||
      !afterGoal ||
      (afterGoal.tokensUsed >= beforeGoal.tokensUsed &&
        afterGoal.timeUsedSeconds >= beforeGoal.timeUsedSeconds);
    const createdAtPreserved =
      operation !== "attach" ||
      !beforeGoal ||
      !afterGoal ||
      afterGoal.createdAt === beforeGoal.createdAt;
    const noThreadStartOrFork =
      requestMethods.every((method) => !forbiddenControlMethods.has(method)) &&
      !notificationMethods.includes("thread/started");
    const noModelTurnStarted =
      newTurnIds.length === 0 && !notificationMethods.includes("turn/started");
    const attachIsReadOnly = operation !== "attach" || !requestMethods.includes("thread/goal/set");
    const notificationThreadsMatch = notificationThreadIds.every(
      (notificationThreadId) => notificationThreadId === threadId,
    );

    const errors: string[] = [];
    if (outcome === "unavailable") {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_NOT_FOUND");
    }
    if (!sameThread) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_THREAD_MISMATCH");
    }
    if (!objectivePreserved) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_OBJECTIVE_CHANGED");
    }
    if (!usageNotReset) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_USAGE_RESET");
    }
    if (!createdAtPreserved) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_CREATED_AT_RESET");
    }
    if (!noThreadStartOrFork) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_CREATED_THREAD");
    }
    if (!noModelTurnStarted) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_STARTED_MODEL_TURN");
    }
    if (!attachIsReadOnly) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_ATTACH_WROTE_STATE");
    }
    if (!notificationThreadsMatch) {
      errors.push("GOAL_PROGRESS_NATIVE_GOAL_NOTIFICATION_THREAD_MISMATCH");
    }

    return {
      schemaVersion: 1,
      operation,
      outcome,
      passed: errors.length === 0,
      mutationAttempted,
      beforeGoal,
      afterGoal,
      beforeTurnIds,
      afterTurnIds,
      newTurnIds,
      requestMethods,
      notificationMethods,
      notificationThreadIds,
      assertions: {
        sameThread,
        objectivePreserved,
        usageNotReset,
        createdAtPreserved,
        objectiveConflictProtected,
        attachIsReadOnly,
        notificationThreadsMatch,
        noThreadStartOrFork,
        noModelTurnStarted,
      },
      errors,
    };
  } catch (error) {
    throw new Error(`GOAL_PROGRESS_NATIVE_GOAL_PROBE_FAILED: ${errorMessage(error)}`);
  } finally {
    await client.close();
  }
}
