import { chmod, unlink } from "node:fs/promises";
import { createServer, type Server, type Socket } from "node:net";
import { isAbsolute } from "node:path";
import type { GoalProgressViewModel } from "../../contracts/src/index.js";
import {
  GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES,
  GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
  type GoalProgressIpcClientKind,
  type GoalProgressIpcRequest,
  GoalProgressIpcRequestSchema,
  type GoalProgressIpcResponse,
} from "./protocol.js";

const GOAL_PROGRESS_IPC_IDLE_TIMEOUT_MS = 10_000;
const GOAL_PROGRESS_IPC_MAX_QUEUED_MESSAGES = 64;
const GOAL_PROGRESS_IPC_MAX_CONNECTIONS = 64;
const GOAL_PROGRESS_IPC_MAX_IN_FLIGHT = 256;

export interface GoalProgressIpcHandlerResult {
  readonly revision: number | null;
  readonly result: unknown;
  readonly afterResponse?: () => Promise<void> | void;
}

export interface GoalProgressIpcConnectionContext {
  readonly clientKind: GoalProgressIpcClientKind;
  readonly clientVersion: string;
}

export type GoalProgressIpcHandler = (
  request: Exclude<GoalProgressIpcRequest, { method: "hello" }>,
  context: GoalProgressIpcConnectionContext,
) => Promise<GoalProgressIpcHandlerResult>;

export class GoalProgressIpcHandlerError extends Error {
  readonly code: string;
  readonly revision: number | null;
  readonly currentViewModel: GoalProgressViewModel | undefined;

  constructor(
    code: string,
    message: string,
    revision: number | null = null,
    currentViewModel?: GoalProgressViewModel,
    cause?: unknown,
  ) {
    super(message, cause === undefined ? undefined : { cause });
    this.name = "GoalProgressIpcHandlerError";
    this.code = code;
    this.revision = revision;
    this.currentViewModel = currentViewModel;
  }
}

export interface GoalProgressIpcServerOptions {
  readonly removeStaleSocket?: boolean;
  readonly faults?: {
    readonly afterListen?: () => Promise<void> | void;
  };
}

function responseLine(response: GoalProgressIpcResponse): string {
  return `${JSON.stringify(response)}\n`;
}

function writeSocketLine(socket: Socket, line: string): Promise<void> {
  return new Promise((resolveWrite) => {
    if (socket.destroyed || !socket.writable) {
      resolveWrite();
      return;
    }
    socket.write(line, () => resolveWrite());
  });
}

function errorResponse(
  requestId: string,
  code: string,
  message: string,
  revision: number | null = null,
  currentViewModel?: GoalProgressViewModel,
): GoalProgressIpcResponse {
  return {
    ok: false,
    protocolVersion: GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
    requestId,
    revision,
    code,
    message,
    ...(currentViewModel === undefined ? {} : { currentViewModel }),
  };
}

function looseEnvelope(value: unknown): {
  readonly requestId: string;
  readonly protocolVersion: unknown;
} {
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    const record = value as Record<string, unknown>;
    return {
      requestId:
        typeof record.requestId === "string" && record.requestId.trim()
          ? record.requestId
          : "unknown",
      protocolVersion: record.protocolVersion,
    };
  }
  return { requestId: "unknown", protocolVersion: undefined };
}

export class GoalProgressIpcServer {
  readonly #socketPath: string;
  readonly #handler: GoalProgressIpcHandler;
  readonly #connections = new Set<Socket>();
  readonly #inFlight = new Set<Promise<void>>();
  #server: Server | undefined;
  #acceptingRequests = false;

  constructor(socketPath: string, handler: GoalProgressIpcHandler) {
    if (!isAbsolute(socketPath)) {
      throw new GoalProgressIpcHandlerError(
        "IPC_PATH_INVALID",
        "Goal Progress Helper socket path must be absolute",
      );
    }
    this.#socketPath = socketPath;
    this.#handler = handler;
  }

  async start(options: GoalProgressIpcServerOptions = {}): Promise<void> {
    if (this.#server) {
      throw new GoalProgressIpcHandlerError(
        "IPC_ALREADY_RUNNING",
        "Goal Progress IPC server is already running",
      );
    }
    if (options.removeStaleSocket) {
      await unlink(this.#socketPath).catch((error: unknown) => {
        if (
          !(
            error instanceof Error &&
            "code" in error &&
            (error as NodeJS.ErrnoException).code === "ENOENT"
          )
        ) {
          throw error;
        }
      });
    }
    const server = createServer((socket) => this.#handleConnection(socket));
    this.#server = server;
    let ownsSocket = false;
    try {
      await new Promise<void>((resolveListen, rejectListen) => {
        server.once("error", rejectListen);
        server.listen(this.#socketPath, () => {
          ownsSocket = true;
          server.off("error", rejectListen);
          resolveListen();
        });
      });
      await options.faults?.afterListen?.();
      await chmod(this.#socketPath, 0o600);
      this.#acceptingRequests = true;
    } catch (error) {
      this.#acceptingRequests = false;
      this.#server = undefined;
      for (const connection of this.#connections) {
        connection.destroy();
      }
      this.#connections.clear();
      if (server.listening) {
        await new Promise<void>((resolveClose) => server.close(() => resolveClose()));
      }
      if (ownsSocket) {
        await unlink(this.#socketPath).catch(() => undefined);
      }
      throw error;
    }
  }

  #trackInFlight(operation: Promise<void>): void {
    this.#inFlight.add(operation);
    void operation.finally(() => {
      this.#inFlight.delete(operation);
    });
  }

  async #drainInFlight(): Promise<void> {
    while (this.#inFlight.size > 0) {
      await Promise.all(this.#inFlight);
    }
  }

  #handleConnection(socket: Socket): void {
    if (!this.#acceptingRequests || this.#connections.size >= GOAL_PROGRESS_IPC_MAX_CONNECTIONS) {
      socket.destroy();
      return;
    }
    this.#connections.add(socket);
    socket.setTimeout(GOAL_PROGRESS_IPC_IDLE_TIMEOUT_MS, () => socket.destroy());
    let buffer = Buffer.alloc(0);
    let handshakeComplete = false;
    let connectionContext: GoalProgressIpcConnectionContext | undefined;
    let chain = Promise.resolve();
    let acceptingData = true;
    let terminated = false;
    let queuedMessages = 0;
    const disconnect = () => {
      acceptingData = false;
      terminated = true;
      buffer = Buffer.alloc(0);
    };
    const close = () => {
      disconnect();
      this.#connections.delete(socket);
    };
    const terminate = (response: GoalProgressIpcResponse) => {
      if (terminated) {
        return;
      }
      acceptingData = false;
      terminated = true;
      buffer = Buffer.alloc(0);
      socket.end(responseLine(response));
    };
    const queueSizeError = () => {
      acceptingData = false;
      buffer = Buffer.alloc(0);
      chain = chain.then(() =>
        terminate(
          errorResponse("unknown", "IPC_MESSAGE_TOO_LARGE", "IPC request exceeded the size limit"),
        ),
      );
    };
    socket.on("end", disconnect);
    socket.on("close", close);
    socket.on("error", disconnect);
    socket.on("data", (chunk: Buffer) => {
      if (!this.#acceptingRequests) {
        socket.destroy();
        return;
      }
      if (!acceptingData) {
        return;
      }
      buffer = Buffer.concat([buffer, chunk]);
      let newline = buffer.indexOf(0x0a);
      while (newline >= 0) {
        if (this.#inFlight.size >= GOAL_PROGRESS_IPC_MAX_IN_FLIGHT) {
          terminate(
            errorResponse("unknown", "IPC_SERVER_BUSY", "IPC server has too many pending requests"),
          );
          return;
        }
        if (queuedMessages >= GOAL_PROGRESS_IPC_MAX_QUEUED_MESSAGES) {
          terminate(
            errorResponse("unknown", "IPC_QUEUE_LIMIT", "IPC connection queued too many requests"),
          );
          return;
        }
        if (newline + 1 > GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES) {
          queueSizeError();
          return;
        }
        const line = buffer.subarray(0, newline).toString("utf8");
        buffer = buffer.subarray(newline + 1);
        queuedMessages += 1;
        const operation = chain
          .then(async () => {
            if (terminated) {
              return;
            }
            let value: unknown;
            try {
              value = JSON.parse(line);
            } catch {
              terminate(
                errorResponse("unknown", "IPC_REQUEST_INVALID", "IPC request is not valid JSON"),
              );
              return;
            }
            const envelope = looseEnvelope(value);
            if (envelope.protocolVersion !== GOAL_PROGRESS_IPC_PROTOCOL_VERSION) {
              terminate(
                errorResponse(
                  envelope.requestId,
                  "PROTOCOL_VERSION_MISMATCH",
                  "IPC protocol version is not supported",
                ),
              );
              return;
            }
            const parsed = GoalProgressIpcRequestSchema.safeParse(value);
            if (!parsed.success) {
              await writeSocketLine(
                socket,
                responseLine(
                  errorResponse(
                    envelope.requestId,
                    "IPC_REQUEST_INVALID",
                    parsed.error.issues[0]?.message ?? "IPC request is invalid",
                  ),
                ),
              );
              return;
            }
            const request = parsed.data;
            if (!handshakeComplete) {
              if (request.method !== "hello") {
                terminate(
                  errorResponse(
                    request.requestId,
                    "HANDSHAKE_REQUIRED",
                    "IPC hello must be the first request",
                  ),
                );
                return;
              }
              handshakeComplete = true;
              connectionContext = {
                clientKind: request.params.clientKind,
                clientVersion: request.params.clientVersion,
              };
              await writeSocketLine(
                socket,
                responseLine({
                  ok: true,
                  protocolVersion: GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
                  requestId: request.requestId,
                  revision: null,
                  result: { accepted: true },
                }),
              );
              return;
            }
            if (request.method === "hello") {
              await writeSocketLine(
                socket,
                responseLine(
                  errorResponse(
                    request.requestId,
                    "HANDSHAKE_ALREADY_COMPLETE",
                    "IPC hello can be sent only once",
                  ),
                ),
              );
              return;
            }
            try {
              if (!connectionContext) {
                throw new GoalProgressIpcHandlerError(
                  "HANDSHAKE_REQUIRED",
                  "IPC connection context is unavailable",
                );
              }
              const handled = await this.#handler(request, connectionContext);
              const successLine = responseLine({
                ok: true,
                protocolVersion: GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
                requestId: request.requestId,
                revision: handled.revision,
                result: handled.result,
              });
              const responseIsSuccess =
                Buffer.byteLength(successLine) <= GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES;
              await writeSocketLine(
                socket,
                responseIsSuccess
                  ? successLine
                  : responseLine(
                      errorResponse(
                        request.requestId,
                        "IPC_RESPONSE_TOO_LARGE",
                        "IPC response exceeded the size limit",
                        handled.revision,
                      ),
                    ),
              );
              if (responseIsSuccess && handled.afterResponse) {
                try {
                  const afterResponse = Promise.resolve(handled.afterResponse()).catch(
                    () => undefined,
                  );
                  this.#trackInFlight(afterResponse);
                } catch {
                  // The successful response is already visible to the client.
                }
              }
            } catch (error) {
              const handledError =
                error instanceof GoalProgressIpcHandlerError
                  ? error
                  : new GoalProgressIpcHandlerError(
                      "INTERNAL_ERROR",
                      "Goal Progress Helper request failed",
                    );
              const handledErrorLine = responseLine(
                errorResponse(
                  request.requestId,
                  handledError.code,
                  handledError.message,
                  handledError.revision,
                  handledError.currentViewModel,
                ),
              );
              await writeSocketLine(
                socket,
                Buffer.byteLength(handledErrorLine) <= GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES
                  ? handledErrorLine
                  : responseLine(
                      errorResponse(
                        request.requestId,
                        "IPC_RESPONSE_TOO_LARGE",
                        "IPC error response exceeded the size limit",
                        handledError.revision,
                      ),
                    ),
              );
            }
          })
          .catch(() => {
            terminate(
              errorResponse("unknown", "INTERNAL_ERROR", "Goal Progress Helper request failed"),
            );
          })
          .finally(() => {
            queuedMessages -= 1;
          });
        chain = operation;
        this.#trackInFlight(operation);
        newline = buffer.indexOf(0x0a);
      }
      if (buffer.length > GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES) {
        queueSizeError();
      }
    });
  }

  async stop(): Promise<void> {
    const server = this.#server;
    if (!server) {
      return;
    }
    this.#acceptingRequests = false;
    this.#server = undefined;
    const closePromise = new Promise<void>((resolveClose) => server.close(() => resolveClose()));
    await this.#drainInFlight();
    for (const socket of this.#connections) {
      socket.destroy();
    }
    this.#connections.clear();
    await closePromise;
    await unlink(this.#socketPath).catch(() => undefined);
  }
}
