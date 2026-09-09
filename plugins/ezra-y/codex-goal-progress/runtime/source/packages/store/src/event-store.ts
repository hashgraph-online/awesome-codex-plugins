import { chmod, open, readFile, truncate } from "node:fs/promises";
import { z } from "zod";
import {
  GOAL_CONTRACT_SCHEMA_VERSION,
  type GoalContract,
  type GoalContractAny,
  GoalContractSchema,
  GoalContractV1Schema,
  type GoalProgressCommand,
  GoalProgressCommandSchema,
  type GoalProgressEvent,
  GoalProgressEventSchema,
} from "../../contracts/src/index.js";
import {
  applyGoalProgressCommand,
  type GoalProgressCoreFailure,
  reduceGoalProgressEvent,
} from "../../core/src/index.js";
import {
  appendDurableLine,
  atomicWriteFile,
  cleanupAtomicTemporaryFiles,
  ensurePrivateDirectory,
} from "./atomic.js";
import { GoalProgressStoreError } from "./errors.js";
import type { GoalProgressLogger, GoalProgressLogInput } from "./logger.js";
import { type GoalProgressPaths, resolveGoalProgressSessionPaths } from "./paths.js";

const GoalProgressSnapshotSchema = z
  .object({
    schemaVersion: z.union([z.literal(1), z.literal(GOAL_CONTRACT_SCHEMA_VERSION)]),
    sessionId: z.string().trim().min(1),
    revision: z.number().int().nonnegative(),
    contract: z.union([GoalContractV1Schema, GoalContractSchema]),
  })
  .strict()
  .superRefine((snapshot, context) => {
    if (snapshot.schemaVersion !== snapshot.contract.schemaVersion) {
      context.addIssue({
        code: "custom",
        message: "Snapshot schemaVersion does not match its Contract",
      });
    }
    if (
      snapshot.sessionId !== snapshot.contract.sessionId ||
      snapshot.revision !== snapshot.contract.revision
    ) {
      context.addIssue({
        code: "custom",
        message: "Snapshot identity does not match its Contract",
      });
    }
  });

export interface GoalEventStoreFaults {
  beforeAppend?(): Promise<void> | void;
  beforeSnapshotRename?(): Promise<void> | void;
}

export interface GoalEventStoreOptions {
  readonly faults?: GoalEventStoreFaults;
  readonly logger?: GoalProgressLogger;
}

export interface GoalInitializationMetadata {
  readonly eventId: string;
  readonly requestId: string;
  readonly turnId: string;
  readonly occurredAt: string;
  readonly source: GoalProgressEvent["source"];
}

export interface GoalReplacementExpectation {
  readonly contractId: string;
  readonly revision: number;
}

export interface GoalEventStoreLoadResult {
  readonly contract: GoalContractAny | null;
  readonly eventCount: number;
  readonly snapshotRecovered: boolean;
  readonly tornTailRepaired: boolean;
}

export interface GoalEventStoreWriteSuccess {
  readonly ok: true;
  readonly contract: GoalContractAny;
  readonly event: GoalProgressEvent;
  readonly duplicate: boolean;
}

export type GoalEventStoreWriteResult = GoalEventStoreWriteSuccess | GoalProgressCoreFailure;

interface ReplayedSession {
  readonly contract: GoalContractAny | null;
  readonly events: readonly GoalProgressEvent[];
  readonly eventsById: ReadonlyMap<string, GoalProgressEvent>;
  readonly eventsByRequestId: ReadonlyMap<string, GoalProgressEvent>;
  readonly snapshotRecovered: boolean;
  readonly tornTailRepaired: boolean;
}

function hasCode(error: unknown, code: string): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === code
  );
}

async function appendMissingNewline(path: string): Promise<void> {
  const file = await open(path, "a", 0o600);
  try {
    await file.writeFile("\n", "utf8");
    await file.sync();
  } finally {
    await file.close();
  }
  await chmod(path, 0o600);
}

async function truncateDurably(path: string, length: number): Promise<void> {
  await truncate(path, length);
  const file = await open(path, "r+");
  try {
    await file.sync();
  } finally {
    await file.close();
  }
  await chmod(path, 0o600);
}

async function readEvents(path: string): Promise<{
  readonly events: readonly GoalProgressEvent[];
  readonly tornTailRepaired: boolean;
}> {
  let contents: Buffer;
  try {
    contents = await readFile(path);
  } catch (error) {
    if (hasCode(error, "ENOENT")) {
      return { events: [], tornTailRepaired: false };
    }
    throw new GoalProgressStoreError("STORE_IO_FAILED", "Could not read the event log", {
      cause: error,
    });
  }
  if (contents.length === 0) {
    return { events: [], tornTailRepaired: false };
  }

  const finalNewline = contents.lastIndexOf(0x0a);
  const hasTrailingLine = finalNewline !== contents.length - 1;
  const completeEnd = hasTrailingLine ? finalNewline + 1 : contents.length;
  const completeLines = contents.subarray(0, completeEnd).toString("utf8").split("\n");
  if (completeLines.at(-1) === "") {
    completeLines.pop();
  }
  let trailingEvent: GoalProgressEvent | undefined;
  let tornTailRepaired = false;

  if (hasTrailingLine) {
    const trailing = contents.subarray(completeEnd).toString("utf8");
    let trailingValue: unknown;
    try {
      trailingValue = JSON.parse(trailing);
    } catch {
      await truncateDurably(path, completeEnd);
      tornTailRepaired = true;
    }
    if (!tornTailRepaired) {
      const parsedTrailing = GoalProgressEventSchema.safeParse(trailingValue);
      if (!parsedTrailing.success) {
        throw new GoalProgressStoreError("EVENT_LOG_CORRUPT", "Event log final line is invalid", {
          cause: parsedTrailing.error,
        });
      }
      trailingEvent = parsedTrailing.data;
      await appendMissingNewline(path);
      tornTailRepaired = true;
    }
  }

  const events: GoalProgressEvent[] = [];
  for (const [index, line] of completeLines.entries()) {
    try {
      events.push(GoalProgressEventSchema.parse(JSON.parse(line)));
    } catch (error) {
      throw new GoalProgressStoreError(
        "EVENT_LOG_CORRUPT",
        `Event log line ${index + 1} is invalid`,
        { cause: error },
      );
    }
  }
  if (trailingEvent) {
    events.push(trailingEvent);
  }
  return { events, tornTailRepaired };
}

function replayEvents(events: readonly GoalProgressEvent[]): {
  readonly contract: GoalContractAny | null;
  readonly eventsById: ReadonlyMap<string, GoalProgressEvent>;
  readonly eventsByRequestId: ReadonlyMap<string, GoalProgressEvent>;
} {
  let contract: GoalContractAny | null = null;
  const eventsById = new Map<string, GoalProgressEvent>();
  const eventsByRequestId = new Map<string, GoalProgressEvent>();
  for (const event of events) {
    if (eventsById.has(event.eventId) || eventsByRequestId.has(event.requestId)) {
      throw new GoalProgressStoreError(
        "EVENT_LOG_CORRUPT",
        "Event log contains a duplicate eventId or requestId",
      );
    }
    const replayed = reduceGoalProgressEvent(contract, event);
    if (!replayed.ok) {
      throw new GoalProgressStoreError(
        "EVENT_LOG_CORRUPT",
        `Event replay failed: ${replayed.code}`,
      );
    }
    contract = replayed.contract;
    eventsById.set(event.eventId, event);
    eventsByRequestId.set(event.requestId, event);
  }
  return { contract, eventsById, eventsByRequestId };
}

async function readSnapshot(path: string): Promise<{
  readonly exists: boolean;
  readonly valid: boolean;
  readonly contract?: GoalContractAny;
}> {
  try {
    const parsed = GoalProgressSnapshotSchema.safeParse(JSON.parse(await readFile(path, "utf8")));
    return parsed.success
      ? { exists: true, valid: true, contract: parsed.data.contract }
      : { exists: true, valid: false };
  } catch (error) {
    if (hasCode(error, "ENOENT")) {
      return { exists: false, valid: false };
    }
    if (error instanceof SyntaxError) {
      return { exists: true, valid: false };
    }
    throw new GoalProgressStoreError("STORE_IO_FAILED", "Could not read the snapshot", {
      cause: error,
    });
  }
}

async function writeSnapshot(
  path: string,
  contract: GoalContractAny,
  faults: GoalEventStoreFaults,
): Promise<void> {
  await atomicWriteFile(
    path,
    `${JSON.stringify(
      {
        schemaVersion: contract.schemaVersion,
        sessionId: contract.sessionId,
        revision: contract.revision,
        contract,
      },
      null,
      2,
    )}\n`,
    faults.beforeSnapshotRename ? { beforeRename: faults.beforeSnapshotRename } : {},
  );
}

function duplicateResult(
  session: ReplayedSession,
  eventId: string,
  requestId: string,
  matchesRequest: (event: GoalProgressEvent) => boolean,
): GoalEventStoreWriteSuccess | undefined {
  const byRequest = session.eventsByRequestId.get(requestId);
  if (byRequest) {
    if (byRequest.eventId !== eventId) {
      throw new GoalProgressStoreError(
        "REQUEST_ID_CONFLICT",
        "requestId was already used with another eventId",
      );
    }
    if (!matchesRequest(byRequest)) {
      throw new GoalProgressStoreError(
        "REQUEST_ID_CONFLICT",
        "requestId was already used with different request content",
      );
    }
    if (!session.contract) {
      throw new GoalProgressStoreError(
        "EVENT_LOG_CORRUPT",
        "Duplicate request exists without a current Contract",
      );
    }
    return {
      ok: true,
      contract: session.contract,
      event: byRequest,
      duplicate: true,
    };
  }
  const byEvent = session.eventsById.get(eventId);
  if (byEvent) {
    throw new GoalProgressStoreError(
      "EVENT_ID_CONFLICT",
      "eventId was already used with another requestId",
    );
  }
  return undefined;
}

function eventEnvelopeMatchesCommand(
  event: GoalProgressEvent,
  command: GoalProgressCommand,
): boolean {
  return (
    event.contractId === command.contractId &&
    event.sessionId === command.sessionId &&
    event.turnId === command.turnId &&
    event.revision === command.expectedRevision + 1 &&
    event.source === command.source
  );
}

function eventMatchesCommand(event: GoalProgressEvent, command: GoalProgressCommand): boolean {
  if (!eventEnvelopeMatchesCommand(event, command)) {
    return false;
  }
  if (command.type === "update-items") {
    return (
      event.type === "contract.items-updated" &&
      JSON.stringify(event.payload.changes) === JSON.stringify(command.changes) &&
      event.payload.activeObjectiveId === command.activeObjectiveId &&
      event.payload.correctionReason === command.correctionReason
    );
  }
  if (command.type === "rescope") {
    return (
      event.type === "contract.rescoped" &&
      event.payload.reason === command.reason.trim() &&
      JSON.stringify(event.payload.objectives) === JSON.stringify(command.objectives)
    );
  }
  if (command.type === "retarget-rescope") {
    return (
      event.type === "contract.retargeted" &&
      event.payload.reason === command.reason.trim() &&
      JSON.stringify(event.payload.nativeGoalBinding) ===
        JSON.stringify(command.nativeGoalBinding) &&
      JSON.stringify(event.payload.nativeGoal) === JSON.stringify(command.nativeGoal) &&
      JSON.stringify(event.payload.objectives) === JSON.stringify(command.objectives)
    );
  }
  if (command.type === "set-phase") {
    return event.type === "contract.phase-changed" && event.payload.phase === command.phase;
  }
  return (
    event.type === "native-goal.synced" &&
    JSON.stringify(event.payload.nativeGoal) === JSON.stringify(command.nativeGoal)
  );
}

function eventMatchesInitialization(
  event: GoalProgressEvent,
  contract: GoalContractAny,
  metadata: GoalInitializationMetadata,
): boolean {
  if (event.type !== "contract.initialized") {
    return false;
  }
  const {
    createdAt: _eventCreatedAt,
    updatedAt: _eventUpdatedAt,
    ...eventContract
  } = event.payload.contract;
  const {
    createdAt: _requestCreatedAt,
    updatedAt: _requestUpdatedAt,
    ...requestContract
  } = contract;
  return (
    event.contractId === contract.contractId &&
    event.sessionId === contract.sessionId &&
    event.turnId === metadata.turnId &&
    event.revision === contract.revision &&
    event.source === metadata.source &&
    JSON.stringify(eventContract) === JSON.stringify(requestContract)
  );
}

function eventMatchesReplacement(
  event: GoalProgressEvent,
  contract: GoalContract,
  metadata: GoalInitializationMetadata,
  previous: GoalReplacementExpectation,
): boolean {
  return (
    event.type === "contract.replaced" &&
    event.contractId === contract.contractId &&
    event.sessionId === contract.sessionId &&
    event.turnId === metadata.turnId &&
    event.revision === contract.revision &&
    event.source === metadata.source &&
    event.payload.previousContractId === previous.contractId &&
    event.payload.previousRevision === previous.revision &&
    JSON.stringify(event.payload.contract) === JSON.stringify(contract)
  );
}

export class GoalEventStore {
  readonly #paths: GoalProgressPaths;
  readonly #faults: GoalEventStoreFaults;
  readonly #logger: GoalProgressLogger | undefined;
  readonly #queues = new Map<string, Promise<void>>();

  constructor(paths: GoalProgressPaths, options: GoalEventStoreOptions = {}) {
    this.#paths = paths;
    this.#faults = options.faults ?? {};
    this.#logger = options.logger;
  }

  async #log(input: GoalProgressLogInput): Promise<void> {
    await this.#logger?.write(input).catch(() => undefined);
  }

  async #serialize<T>(sessionId: string, operation: () => Promise<T>): Promise<T> {
    const key = resolveGoalProgressSessionPaths(this.#paths, sessionId).sessionKey;
    const previous = this.#queues.get(key) ?? Promise.resolve();
    let releaseQueue!: () => void;
    const current = new Promise<void>((resolveQueue) => {
      releaseQueue = resolveQueue;
    });
    const tail = previous.then(() => current);
    this.#queues.set(key, tail);
    await previous;
    try {
      return await operation();
    } finally {
      releaseQueue();
      if (this.#queues.get(key) === tail) {
        this.#queues.delete(key);
      }
    }
  }

  async #load(sessionId: string): Promise<ReplayedSession> {
    const paths = resolveGoalProgressSessionPaths(this.#paths, sessionId);
    try {
      await ensurePrivateDirectory(paths.directory);
      await cleanupAtomicTemporaryFiles(paths.directory, "snapshot.json");
    } catch (error) {
      throw new GoalProgressStoreError(
        "STORE_IO_FAILED",
        "Could not prepare the Session state directory",
        { cause: error },
      );
    }
    const eventRead = await readEvents(paths.eventsPath);
    const replayed = replayEvents(eventRead.events);
    const snapshot = await readSnapshot(paths.snapshotPath);

    if (eventRead.events.length === 0 && snapshot.exists) {
      throw new GoalProgressStoreError(
        "EVENT_LOG_MISSING",
        "Snapshot exists without its source event log",
      );
    }
    if (replayed.contract && replayed.contract.sessionId !== sessionId) {
      throw new GoalProgressStoreError("EVENT_LOG_CORRUPT", "Event log belongs to another Session");
    }

    const snapshotMatches =
      replayed.contract !== null &&
      snapshot.valid &&
      JSON.stringify(snapshot.contract) === JSON.stringify(replayed.contract);
    const snapshotRecovered = replayed.contract !== null && !snapshotMatches;
    if (snapshotRecovered && replayed.contract) {
      try {
        await writeSnapshot(paths.snapshotPath, replayed.contract, {});
      } catch (error) {
        throw new GoalProgressStoreError(
          "STORE_IO_FAILED",
          "Could not recover the snapshot from its event log",
          { cause: error },
        );
      }
    }
    if (replayed.contract && (snapshotRecovered || eventRead.tornTailRepaired)) {
      await this.#log({
        level: "warn",
        event: "store.recovered",
        sessionKey: paths.sessionKey,
        contractId: replayed.contract.contractId,
        revision: replayed.contract.revision,
        count: eventRead.events.length,
      });
    }

    return {
      contract: replayed.contract,
      events: eventRead.events,
      eventsById: replayed.eventsById,
      eventsByRequestId: replayed.eventsByRequestId,
      snapshotRecovered,
      tornTailRepaired: eventRead.tornTailRepaired,
    };
  }

  async load(sessionId: string): Promise<GoalEventStoreLoadResult> {
    return this.#serialize(sessionId, async () => {
      const session = await this.#load(sessionId);
      return {
        contract: session.contract,
        eventCount: session.events.length,
        snapshotRecovered: session.snapshotRecovered,
        tornTailRepaired: session.tornTailRepaired,
      };
    });
  }

  async initialize(
    contractInput: GoalContract,
    metadata: GoalInitializationMetadata,
  ): Promise<GoalEventStoreWriteSuccess> {
    const contractResult = GoalContractSchema.safeParse(contractInput);
    if (!contractResult.success) {
      throw new GoalProgressStoreError(
        "STORE_CONTRACT_INVALID",
        contractResult.error.issues[0]?.message ?? "Goal Contract is invalid",
      );
    }
    const contract = contractResult.data;
    return this.#serialize(contract.sessionId, async () => {
      const session = await this.#load(contract.sessionId);
      const duplicate = duplicateResult(session, metadata.eventId, metadata.requestId, (event) =>
        eventMatchesInitialization(event, contract, metadata),
      );
      if (duplicate) {
        await this.#log({
          level: "info",
          event: "store.duplicate",
          sessionKey: resolveGoalProgressSessionPaths(this.#paths, contract.sessionId).sessionKey,
          contractId: duplicate.contract.contractId,
          revision: duplicate.contract.revision,
        });
        return duplicate;
      }
      if (session.contract) {
        throw new GoalProgressStoreError(
          "STORE_ALREADY_INITIALIZED",
          "Session already has a Goal Contract",
        );
      }
      const eventResult = GoalProgressEventSchema.safeParse({
        schemaVersion: contract.schemaVersion,
        eventId: metadata.eventId,
        requestId: metadata.requestId,
        contractId: contract.contractId,
        sessionId: contract.sessionId,
        turnId: metadata.turnId,
        revision: contract.revision,
        occurredAt: metadata.occurredAt,
        source: metadata.source,
        type: "contract.initialized",
        payload: { contract },
      });
      if (!eventResult.success) {
        throw new GoalProgressStoreError(
          "STORE_COMMAND_INVALID",
          eventResult.error.issues[0]?.message ?? "Initialization metadata is invalid",
        );
      }
      const event = eventResult.data;
      const paths = resolveGoalProgressSessionPaths(this.#paths, contract.sessionId);
      try {
        await this.#faults.beforeAppend?.();
        await appendDurableLine(paths.eventsPath, JSON.stringify(event));
      } catch (error) {
        throw new GoalProgressStoreError(
          "STORE_IO_FAILED",
          "Could not append the initialization event",
          { cause: error },
        );
      }
      try {
        await writeSnapshot(paths.snapshotPath, contract, this.#faults);
      } catch (error) {
        throw new GoalProgressStoreError(
          "SNAPSHOT_WRITE_FAILED_AFTER_COMMIT",
          "Initialization event committed but snapshot write failed",
          { cause: error, committedRevision: contract.revision },
        );
      }
      await this.#log({
        level: "info",
        event: "store.initialized",
        sessionKey: paths.sessionKey,
        contractId: contract.contractId,
        revision: contract.revision,
      });
      return { ok: true, contract, event, duplicate: false };
    });
  }

  async replace(
    contractInput: GoalContract,
    metadata: GoalInitializationMetadata,
    previous: GoalReplacementExpectation,
  ): Promise<GoalEventStoreWriteSuccess> {
    const contractResult = GoalContractSchema.safeParse(contractInput);
    if (!contractResult.success) {
      throw new GoalProgressStoreError(
        "STORE_CONTRACT_INVALID",
        contractResult.error.issues[0]?.message ?? "Replacement Goal Contract is invalid",
      );
    }
    const contract = contractResult.data;
    return this.#serialize(contract.sessionId, async () => {
      const session = await this.#load(contract.sessionId);
      const duplicate = duplicateResult(session, metadata.eventId, metadata.requestId, (event) =>
        eventMatchesReplacement(event, contract, metadata, previous),
      );
      if (duplicate) {
        await this.#log({
          level: "info",
          event: "store.duplicate",
          sessionKey: resolveGoalProgressSessionPaths(this.#paths, contract.sessionId).sessionKey,
          contractId: duplicate.contract.contractId,
          revision: duplicate.contract.revision,
        });
        return duplicate;
      }
      if (!session.contract) {
        throw new GoalProgressStoreError(
          "STORE_NOT_INITIALIZED",
          "Session has no Goal Contract to replace",
        );
      }
      if (
        session.contract.contractId !== previous.contractId ||
        session.contract.revision !== previous.revision
      ) {
        throw new GoalProgressStoreError(
          "STORE_CONTRACT_INVALID",
          "Stored Contract does not match the replacement expectation",
        );
      }
      const eventResult = GoalProgressEventSchema.safeParse({
        schemaVersion: contract.schemaVersion,
        eventId: metadata.eventId,
        requestId: metadata.requestId,
        contractId: contract.contractId,
        sessionId: contract.sessionId,
        turnId: metadata.turnId,
        revision: contract.revision,
        occurredAt: metadata.occurredAt,
        source: metadata.source,
        type: "contract.replaced",
        payload: {
          previousContractId: previous.contractId,
          previousRevision: previous.revision,
          contract,
        },
      });
      if (!eventResult.success) {
        throw new GoalProgressStoreError(
          "STORE_COMMAND_INVALID",
          eventResult.error.issues[0]?.message ?? "Replacement metadata is invalid",
        );
      }
      const event = eventResult.data;
      const reduced = reduceGoalProgressEvent(session.contract, event);
      if (!reduced.ok) {
        throw new GoalProgressStoreError(
          "STORE_CONTRACT_INVALID",
          `Replacement event failed: ${reduced.code}`,
        );
      }
      const paths = resolveGoalProgressSessionPaths(this.#paths, contract.sessionId);
      try {
        await this.#faults.beforeAppend?.();
        await appendDurableLine(paths.eventsPath, JSON.stringify(event));
      } catch (error) {
        throw new GoalProgressStoreError(
          "STORE_IO_FAILED",
          "Could not append the replacement event",
          { cause: error },
        );
      }
      try {
        await writeSnapshot(paths.snapshotPath, reduced.contract, this.#faults);
      } catch (error) {
        throw new GoalProgressStoreError(
          "SNAPSHOT_WRITE_FAILED_AFTER_COMMIT",
          "Replacement event committed but snapshot write failed",
          { cause: error, committedRevision: reduced.contract.revision },
        );
      }
      await this.#log({
        level: "info",
        event: "store.replaced",
        sessionKey: paths.sessionKey,
        contractId: reduced.contract.contractId,
        revision: reduced.contract.revision,
      });
      return {
        ok: true,
        contract: reduced.contract,
        event,
        duplicate: false,
      };
    });
  }

  async persistMigrated(
    contractInput: GoalContract,
    metadata: GoalInitializationMetadata,
  ): Promise<GoalEventStoreWriteSuccess> {
    const contractResult = GoalContractSchema.safeParse(contractInput);
    if (!contractResult.success) {
      throw new GoalProgressStoreError(
        "STORE_CONTRACT_INVALID",
        contractResult.error.issues[0]?.message ?? "Migrated Goal Contract is invalid",
      );
    }
    const contract = contractResult.data;
    return this.#serialize(contract.sessionId, async () => {
      const session = await this.#load(contract.sessionId);
      const duplicate = duplicateResult(session, metadata.eventId, metadata.requestId, (event) => {
        return (
          event.type === "contract.migrated" &&
          event.revision === contract.revision &&
          JSON.stringify(event.payload.contract) === JSON.stringify(contract)
        );
      });
      if (duplicate) {
        return duplicate;
      }
      if (!session.contract) {
        throw new GoalProgressStoreError("STORE_NOT_INITIALIZED", "Session has no Goal Contract");
      }
      if (session.contract.schemaVersion === GOAL_CONTRACT_SCHEMA_VERSION) {
        const last = session.events.at(-1);
        if (!last) {
          throw new GoalProgressStoreError(
            "EVENT_LOG_CORRUPT",
            "Schema v2 Contract exists without events",
          );
        }
        return { ok: true, contract: session.contract, event: last, duplicate: true };
      }
      if (
        session.contract.contractId !== contract.contractId ||
        session.contract.revision !== contract.revision ||
        session.contract.sessionId !== contract.sessionId
      ) {
        throw new GoalProgressStoreError(
          "STORE_CONTRACT_INVALID",
          "Migrated Contract does not preserve the stored identity and revision",
        );
      }
      const eventResult = GoalProgressEventSchema.safeParse({
        schemaVersion: GOAL_CONTRACT_SCHEMA_VERSION,
        eventId: metadata.eventId,
        requestId: metadata.requestId,
        contractId: contract.contractId,
        sessionId: contract.sessionId,
        turnId: metadata.turnId,
        revision: contract.revision,
        occurredAt: metadata.occurredAt,
        source: metadata.source,
        type: "contract.migrated",
        payload: {
          fromVersion: 1,
          toVersion: GOAL_CONTRACT_SCHEMA_VERSION,
          contract,
        },
      });
      if (!eventResult.success) {
        throw new GoalProgressStoreError(
          "STORE_COMMAND_INVALID",
          eventResult.error.issues[0]?.message ?? "Migration event is invalid",
        );
      }
      const event = eventResult.data;
      const paths = resolveGoalProgressSessionPaths(this.#paths, contract.sessionId);
      try {
        await this.#faults.beforeAppend?.();
        await appendDurableLine(paths.eventsPath, JSON.stringify(event));
      } catch (error) {
        throw new GoalProgressStoreError(
          "STORE_IO_FAILED",
          "Could not append the migration event",
          { cause: error },
        );
      }
      try {
        await writeSnapshot(paths.snapshotPath, contract, this.#faults);
      } catch (error) {
        throw new GoalProgressStoreError(
          "SNAPSHOT_WRITE_FAILED_AFTER_COMMIT",
          "Migration event committed but snapshot write failed",
          { cause: error, committedRevision: contract.revision },
        );
      }
      await this.#log({
        level: "info",
        event: "store.migrated",
        sessionKey: paths.sessionKey,
        contractId: contract.contractId,
        revision: contract.revision,
      });
      return { ok: true, contract, event, duplicate: false };
    });
  }

  async apply(commandInput: GoalProgressCommand): Promise<GoalEventStoreWriteResult> {
    const commandResult = GoalProgressCommandSchema.safeParse(commandInput);
    if (!commandResult.success) {
      throw new GoalProgressStoreError(
        "STORE_COMMAND_INVALID",
        commandResult.error.issues[0]?.message ?? "Goal Progress command is invalid",
      );
    }
    const command = commandResult.data;
    return this.#serialize(command.sessionId, async () => {
      const session = await this.#load(command.sessionId);
      const duplicate = duplicateResult(session, command.eventId, command.requestId, (event) =>
        eventMatchesCommand(event, command),
      );
      if (duplicate) {
        await this.#log({
          level: "info",
          event: "store.duplicate",
          sessionKey: resolveGoalProgressSessionPaths(this.#paths, command.sessionId).sessionKey,
          contractId: duplicate.contract.contractId,
          revision: duplicate.contract.revision,
        });
        return duplicate;
      }
      if (!session.contract) {
        throw new GoalProgressStoreError("STORE_NOT_INITIALIZED", "Session has no Goal Contract");
      }
      if (session.contract.schemaVersion !== GOAL_CONTRACT_SCHEMA_VERSION) {
        throw new GoalProgressStoreError(
          "STORE_CONTRACT_INVALID",
          "Apply requires a schema v2 Goal Contract",
        );
      }
      const reduced = applyGoalProgressCommand(session.contract, command);
      if (!reduced.ok) {
        return reduced;
      }
      const paths = resolveGoalProgressSessionPaths(this.#paths, command.sessionId);
      try {
        await this.#faults.beforeAppend?.();
        await appendDurableLine(paths.eventsPath, JSON.stringify(reduced.event));
      } catch (error) {
        throw new GoalProgressStoreError(
          "STORE_IO_FAILED",
          "Could not append the Goal Progress event",
          { cause: error },
        );
      }
      try {
        await writeSnapshot(paths.snapshotPath, reduced.contract, this.#faults);
      } catch (error) {
        throw new GoalProgressStoreError(
          "SNAPSHOT_WRITE_FAILED_AFTER_COMMIT",
          "Event committed but snapshot write failed",
          {
            cause: error,
            committedRevision: reduced.contract.revision,
          },
        );
      }
      await this.#log({
        level: "info",
        event: "store.applied",
        sessionKey: paths.sessionKey,
        contractId: reduced.contract.contractId,
        revision: reduced.contract.revision,
      });
      return {
        ok: true,
        contract: reduced.contract,
        event: reduced.event,
        duplicate: false,
      };
    });
  }
}
