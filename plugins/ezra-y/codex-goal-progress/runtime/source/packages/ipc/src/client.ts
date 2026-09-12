import { Buffer } from "node:buffer";
import { randomUUID } from "node:crypto";
import { createConnection, type Socket } from "node:net";
import { isAbsolute } from "node:path";
import {
  GOAL_PROGRESS_RELEASE_VERSION,
  type GoalProgressViewModel,
} from "../../contracts/src/index.js";
import {
  GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES,
  GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
  type GoalProgressIpcClientKind,
  GoalProgressIpcProtocolMismatchResponseSchema,
  type GoalProgressIpcRequestInput,
  type GoalProgressIpcResponse,
  GoalProgressIpcResponseSchema,
  type GoalProgressIpcSuccessResponse,
} from "./protocol.js";

const REQUEST_ID_SIZE_PLACEHOLDER = "00000000-0000-4000-8000-000000000000";

export function goalProgressIpcRequestBytes(request: GoalProgressIpcRequestInput): number {
  return Buffer.byteLength(
    `${JSON.stringify({
      ...request,
      protocolVersion: GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
      requestId: REQUEST_ID_SIZE_PLACEHOLDER,
    })}\n`,
  );
}

export class GoalProgressIpcClientError extends Error {
  readonly code: string;
  readonly revision: number | null;
  readonly currentViewModel: GoalProgressViewModel | undefined;

  constructor(
    code: string,
    message: string,
    revision: number | null = null,
    currentViewModel?: GoalProgressViewModel,
  ) {
    super(message);
    this.name = "GoalProgressIpcClientError";
    this.code = code;
    this.revision = revision;
    this.currentViewModel = currentViewModel;
  }
}

export interface GoalProgressIpcClientOptions {
  readonly clientKind: GoalProgressIpcClientKind;
  readonly clientVersion?: string;
  readonly timeoutMs?: number;
}

async function connectSocket(path: string, timeoutMs: number): Promise<Socket> {
  return new Promise((resolveSocket, rejectSocket) => {
    const socket = createConnection(path);
    // Operation listeners reject their own Promise. This guard contains a late
    // socket error that can arrive after a write callback has already settled.
    socket.on("error", () => undefined);
    let settled = false;
    const cleanup = () => {
      clearTimeout(timeout);
      socket.off("connect", onConnect);
      socket.off("error", onError);
    };
    const onConnect = () => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      resolveSocket(socket);
    };
    const onError = () => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      rejectSocket(
        new GoalProgressIpcClientError("IPC_UNAVAILABLE", "Goal Progress Helper is unavailable"),
      );
      socket.destroy();
    };
    const timeout = setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      socket.destroy();
      rejectSocket(
        new GoalProgressIpcClientError(
          "IPC_TIMEOUT",
          "Timed out connecting to Goal Progress Helper",
        ),
      );
    }, timeoutMs);
    socket.once("connect", onConnect);
    socket.once("error", onError);
  });
}

function writeLine(socket: Socket, value: unknown, timeoutMs: number): Promise<void> {
  const line = `${JSON.stringify(value)}\n`;
  return new Promise((resolveWrite, rejectWrite) => {
    let settled = false;
    const cleanup = () => {
      clearTimeout(timeout);
      socket.off("error", onError);
    };
    const reject = (error: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      rejectWrite(error);
    };
    const onError = (error: Error) => {
      reject(error);
    };
    const timeout = setTimeout(
      () =>
        reject(
          new GoalProgressIpcClientError("IPC_TIMEOUT", "Goal Progress Helper write timed out"),
        ),
      timeoutMs,
    );
    socket.once("error", onError);
    socket.write(line, (error) => {
      if (error) {
        reject(
          new GoalProgressIpcClientError(
            "IPC_CLOSED",
            "Goal Progress Helper closed during the write",
          ),
        );
        return;
      }
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      resolveWrite();
    });
  });
}

function readOneResponse(socket: Socket, timeoutMs: number): Promise<GoalProgressIpcResponse> {
  return new Promise((resolveResponse, rejectResponse) => {
    let buffer = Buffer.alloc(0);
    const cleanup = () => {
      clearTimeout(timeout);
      socket.off("data", onData);
      socket.off("error", onError);
      socket.off("close", onClose);
    };
    const reject = (error: Error) => {
      cleanup();
      rejectResponse(error);
    };
    const onError = () =>
      reject(
        new GoalProgressIpcClientError("IPC_UNAVAILABLE", "Goal Progress Helper connection failed"),
      );
    const onClose = () =>
      reject(
        new GoalProgressIpcClientError("IPC_CLOSED", "Goal Progress Helper closed the connection"),
      );
    const onData = (chunk: Buffer) => {
      buffer = Buffer.concat([buffer, chunk]);
      if (buffer.length > GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES) {
        reject(
          new GoalProgressIpcClientError(
            "IPC_MESSAGE_TOO_LARGE",
            "Goal Progress Helper response exceeded the size limit",
          ),
        );
        return;
      }
      const newline = buffer.indexOf(0x0a);
      if (newline < 0) {
        return;
      }
      try {
        const value: unknown = JSON.parse(buffer.subarray(0, newline).toString("utf8"));
        const response = GoalProgressIpcResponseSchema.safeParse(value);
        if (response.success) {
          cleanup();
          resolveResponse(response.data);
          return;
        }
        const mismatch = GoalProgressIpcProtocolMismatchResponseSchema.safeParse(value);
        if (mismatch.success) {
          reject(
            new GoalProgressIpcClientError(
              "PROTOCOL_VERSION_MISMATCH",
              `Goal Progress IPC expects protocol ${GOAL_PROGRESS_IPC_PROTOCOL_VERSION}; Helper reported ${mismatch.data.protocolVersion}`,
              mismatch.data.revision,
            ),
          );
          return;
        }
        reject(
          new GoalProgressIpcClientError(
            "IPC_RESPONSE_INVALID",
            "Goal Progress Helper returned an invalid response",
          ),
        );
      } catch {
        reject(
          new GoalProgressIpcClientError(
            "IPC_RESPONSE_INVALID",
            "Goal Progress Helper returned an invalid response",
          ),
        );
      }
    };
    const timeout = setTimeout(
      () =>
        reject(
          new GoalProgressIpcClientError("IPC_TIMEOUT", "Goal Progress Helper response timed out"),
        ),
      timeoutMs,
    );
    socket.on("data", onData);
    socket.once("error", onError);
    socket.once("close", onClose);
  });
}

export class GoalProgressIpcClient {
  readonly #socketPath: string;
  readonly #clientKind: GoalProgressIpcClientKind;
  readonly #clientVersion: string;
  readonly #timeoutMs: number;

  constructor(socketPath: string, options: GoalProgressIpcClientOptions) {
    if (!isAbsolute(socketPath)) {
      throw new GoalProgressIpcClientError(
        "IPC_PATH_INVALID",
        "Goal Progress Helper socket path must be absolute",
      );
    }
    this.#socketPath = socketPath;
    this.#clientKind = options.clientKind;
    this.#clientVersion = options.clientVersion ?? GOAL_PROGRESS_RELEASE_VERSION;
    this.#timeoutMs = options.timeoutMs ?? 5_000;
  }

  async request(request: GoalProgressIpcRequestInput): Promise<GoalProgressIpcSuccessResponse> {
    if (goalProgressIpcRequestBytes(request) > GOAL_PROGRESS_IPC_MAX_MESSAGE_BYTES) {
      throw new GoalProgressIpcClientError(
        "IPC_MESSAGE_TOO_LARGE",
        "Goal Progress Helper request exceeded the size limit",
      );
    }
    const deadlineMs = Date.now() + this.#timeoutMs;
    const remainingTimeout = (): number => {
      const remaining = deadlineMs - Date.now();
      if (remaining <= 0) {
        throw new GoalProgressIpcClientError(
          "IPC_TIMEOUT",
          "Goal Progress Helper request timed out",
        );
      }
      return remaining;
    };
    const socket = await connectSocket(this.#socketPath, remainingTimeout());
    try {
      const helloId = randomUUID();
      await writeLine(
        socket,
        {
          protocolVersion: GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
          requestId: helloId,
          method: "hello",
          params: {
            clientKind: this.#clientKind,
            clientVersion: this.#clientVersion,
          },
        },
        remainingTimeout(),
      );
      const hello = await readOneResponse(socket, remainingTimeout());
      if (!hello.ok) {
        throw new GoalProgressIpcClientError(
          hello.code,
          hello.message,
          hello.revision,
          hello.currentViewModel,
        );
      }

      const requestId = randomUUID();
      await writeLine(
        socket,
        {
          ...request,
          protocolVersion: GOAL_PROGRESS_IPC_PROTOCOL_VERSION,
          requestId,
        },
        remainingTimeout(),
      );
      const response = await readOneResponse(socket, remainingTimeout());
      if (!response.ok) {
        throw new GoalProgressIpcClientError(
          response.code,
          response.message,
          response.revision,
          response.currentViewModel,
        );
      }
      return response;
    } finally {
      socket.end();
      socket.destroy();
    }
  }
}
