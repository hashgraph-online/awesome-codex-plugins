import { type RuntimeIdentity, RuntimeIdentitySchema } from "../../contracts/src/index.js";

export const CURRENT_THREAD_NOT_FOUND = "CURRENT_THREAD_NOT_FOUND";
export const CURRENT_THREAD_AMBIGUOUS = "CURRENT_THREAD_AMBIGUOUS";

const FORBIDDEN_THREAD_CONTROL_METHODS = Object.freeze([
  "thread/start",
  "thread/fork",
  "turn/start",
]);

export type CurrentThreadResolverErrorCode =
  | typeof CURRENT_THREAD_NOT_FOUND
  | typeof CURRENT_THREAD_AMBIGUOUS;

export class CurrentThreadResolverError extends Error {
  readonly code: CurrentThreadResolverErrorCode;

  constructor(code: CurrentThreadResolverErrorCode, message: string) {
    super(message);
    this.name = "CurrentThreadResolverError";
    this.code = code;
  }
}

export interface CurrentThreadResolverInput {
  readonly sessionTreeId: string;
  readonly turnId: string;
  readonly cwd: string;
  readonly model: string;
}

export interface ThreadCatalogEntry {
  readonly threadId: string;
  readonly cwd?: string;
  readonly recencyAt?: number;
}

export interface ThreadCatalog {
  listLoadedThreads(): Promise<readonly ThreadCatalogEntry[]>;
  listThreads(filter?: { readonly cwd?: string }): Promise<readonly ThreadCatalogEntry[]>;
  listTurnIds(threadId: string): Promise<readonly string[]>;
}

export interface CurrentThreadResolver {
  resolve(input: CurrentThreadResolverInput): Promise<RuntimeIdentity>;
}

function uniqueThreadIds(entries: readonly ThreadCatalogEntry[]): string[] {
  const seen = new Set<string>();
  const ids: string[] = [];
  for (const entry of entries) {
    if (!entry.threadId.trim() || seen.has(entry.threadId)) {
      continue;
    }
    seen.add(entry.threadId);
    ids.push(entry.threadId);
  }
  return ids;
}

function cacheKey(input: CurrentThreadResolverInput): string {
  return `${input.sessionTreeId}\0${input.turnId}\0${input.cwd}`;
}

function uniqueNewestSessionTreeId(
  entries: readonly ThreadCatalogEntry[],
  sessionTreeId: string,
): string | undefined {
  const dated = entries.filter(
    (entry): entry is ThreadCatalogEntry & { readonly recencyAt: number } =>
      Number.isFinite(entry.recencyAt),
  );
  if (dated.length === 0) {
    return undefined;
  }
  const newestAt = Math.max(...dated.map((entry) => entry.recencyAt));
  const newestIds = uniqueThreadIds(dated.filter((entry) => entry.recencyAt === newestAt));
  return newestIds.length === 1 && newestIds[0] === sessionTreeId ? sessionTreeId : undefined;
}

function isUnavailableSessionTreeCandidate(error: unknown): boolean {
  return (
    error instanceof Error &&
    /^GOAL_PROGRESS_APP_SERVER_REQUEST_FAILED: thread\/turns\/list: (?:invalid thread id|thread not loaded)(?:\b|:)/iu.test(
      error.message,
    )
  );
}

export function createCurrentThreadResolver(catalog: ThreadCatalog): CurrentThreadResolver {
  const cache = new Map<string, RuntimeIdentity>();

  const matchingThreadIds = async (
    threadIds: readonly string[],
    turnId: string,
  ): Promise<string[]> => {
    const matches: string[] = [];
    for (const threadId of threadIds) {
      const turnIds = await catalog.listTurnIds(threadId);
      if (turnIds.includes(turnId)) {
        matches.push(threadId);
      }
    }
    return matches;
  };

  return {
    async resolve(input: CurrentThreadResolverInput): Promise<RuntimeIdentity> {
      const key = cacheKey(input);
      const cached = cache.get(key);
      if (cached) {
        return cached;
      }

      const loadedIds = uniqueThreadIds(await catalog.listLoadedThreads());
      let matches: string[] = [];
      try {
        const sessionTreeTurnIds = await catalog.listTurnIds(input.sessionTreeId);
        if (sessionTreeTurnIds.includes(input.turnId)) {
          matches.push(input.sessionTreeId);
        }
      } catch (error) {
        if (!isUnavailableSessionTreeCandidate(error)) {
          throw error;
        }
      }
      matches.push(
        ...(await matchingThreadIds(
          loadedIds.filter((threadId) => threadId !== input.sessionTreeId),
          input.turnId,
        )),
      );

      if (matches.length === 0) {
        const listed = await catalog.listThreads({ cwd: input.cwd });
        const cwdEntries = listed.filter(
          (entry) => entry.cwd === undefined || entry.cwd === input.cwd,
        );
        const listedIds = uniqueThreadIds(cwdEntries);
        matches = await matchingThreadIds(listedIds, input.turnId);
        if (matches.length === 0 && loadedIds.length === 0) {
          const newestSessionTreeId = uniqueNewestSessionTreeId(cwdEntries, input.sessionTreeId);
          if (newestSessionTreeId) {
            matches = [newestSessionTreeId];
          }
        }
      }

      if (matches.length === 0) {
        throw new CurrentThreadResolverError(
          CURRENT_THREAD_NOT_FOUND,
          "Current thread could not be proven from loaded or cwd-filtered threads",
        );
      }
      if (matches.length > 1) {
        throw new CurrentThreadResolverError(
          CURRENT_THREAD_AMBIGUOUS,
          "Multiple threads contain the current turn",
        );
      }

      const identity = RuntimeIdentitySchema.parse({
        sessionTreeId: input.sessionTreeId,
        threadId: matches[0],
        turnId: input.turnId,
        model: input.model,
        cwd: input.cwd,
      });
      cache.set(key, identity);
      return identity;
    },
  };
}

export const GOAL_PROGRESS_FORBIDDEN_THREAD_CONTROL_METHODS = FORBIDDEN_THREAD_CONTROL_METHODS;
