// src/observability/codex-master-token-cli.ts
import { createHash as createHash2 } from "node:crypto";

// src/observability/codex-master-token-usage.ts
import { homedir } from "node:os";
import { isAbsolute as isAbsolute2, resolve as resolve2 } from "node:path";

// src/observability/codex-rollout-token-source.ts
import { createHash } from "node:crypto";
import { lstat, open, readdir } from "node:fs/promises";
import { basename, isAbsolute, relative, resolve, sep } from "node:path";
var ROLLOUT_SUBDIRECTORIES = ["sessions", "archived_sessions"];
function fileId(file) {
  return `rollout#${createHash("sha256").update(basename(file)).digest("hex").slice(0, 12)}`;
}
function numeric(value) {
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}
function usage(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const value = raw;
  return {
    totalTokens: numeric(value.total_tokens),
    inputTokens: numeric(value.input_tokens),
    cachedInputTokens: numeric(value.cached_input_tokens),
    cacheWriteInputTokens: numeric(value.cache_write_input_tokens),
    outputTokens: numeric(value.output_tokens),
    reasoningOutputTokens: numeric(value.reasoning_output_tokens)
  };
}
function isWithin(root, file) {
  const pathFromRoot = relative(root, file);
  return pathFromRoot === "" || !pathFromRoot.startsWith(`..${sep}`) && pathFromRoot !== ".." && !isAbsolute(pathFromRoot);
}
function fileIdentity(stats) {
  return {
    device: String(stats.dev),
    inode: String(stats.ino),
    birthtimeMs: stats.birthtimeMs
  };
}
function sameFileIdentity(left, right) {
  return left.device === right.device && left.inode === right.inode && left.birthtimeMs === right.birthtimeMs;
}
async function boundaryFingerprint(file, offset) {
  if (offset === 0) return null;
  const handle = await open(file, "r");
  try {
    const start = Math.max(0, offset - 4096);
    const buffer = Buffer.alloc(offset - start);
    const result2 = await handle.read(buffer, 0, buffer.length, start);
    if (result2.bytesRead !== buffer.length) return null;
    return createHash("sha256").update(String(offset)).update(buffer).digest("hex");
  } finally {
    await handle.close();
  }
}
function validateThreadId(threadId) {
  if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(threadId)) {
    throw new Error("invalid_thread_id");
  }
}
function filenameMatchesThread(file, threadId) {
  const name = basename(file);
  return name.startsWith("rollout-") && name.endsWith(`-${threadId}.jsonl`);
}
function sessionMeta(payload, expectedThreadId) {
  const parentThreadId = typeof payload.parent_thread_id === "string" ? payload.parent_thread_id : null;
  const threadSource = typeof payload.thread_source === "string" ? payload.thread_source : null;
  const id = typeof payload.id === "string" ? payload.id : null;
  const sessionId = typeof payload.session_id === "string" ? payload.session_id : null;
  if (id !== expectedThreadId || sessionId !== null && sessionId !== expectedThreadId || parentThreadId !== null || threadSource !== "user") {
    return null;
  }
  return {
    sessionId,
    parentThreadId,
    threadSource,
    originator: typeof payload.originator === "string" ? payload.originator : null,
    provider: typeof payload.model_provider === "string" ? payload.model_provider : null,
    cliVersion: typeof payload.cli_version === "string" ? payload.cli_version : null
  };
}
async function readSessionMeta(file, expectedThreadId) {
  let pathStats;
  try {
    pathStats = await lstat(file);
  } catch (error) {
    const code = error.code;
    if (code === "ENOENT" || code === "ENOTDIR") return null;
    throw error;
  }
  if (!pathStats.isFile() || pathStats.isSymbolicLink()) return null;
  const handle = await open(file, "r");
  try {
    const stats = await handle.stat();
    if (!sameFileIdentity(fileIdentity(pathStats), fileIdentity(stats))) return null;
    const buffer = Buffer.alloc(Math.min(stats.size, 256 * 1024));
    const result2 = await handle.read(buffer, 0, buffer.length, 0);
    const text = buffer.subarray(0, result2.bytesRead).toString("utf8");
    for (const line of text.split("\n")) {
      if (!line) continue;
      let record;
      try {
        record = JSON.parse(line);
      } catch {
        continue;
      }
      if (record.type !== "session_meta" || !record.payload || typeof record.payload !== "object" || Array.isArray(record.payload)) {
        continue;
      }
      const validated = sessionMeta(record.payload, expectedThreadId);
      if (!validated) return null;
      return {
        sourceFile: file,
        sourceFileId: fileId(file),
        identity: fileIdentity(stats),
        ...validated
      };
    }
    return null;
  } finally {
    await handle.close();
  }
}
async function findFilenameCandidates(root, threadId) {
  let rootStats;
  try {
    rootStats = await lstat(root);
  } catch (error) {
    const code = error.code;
    if (code === "ENOENT" || code === "ENOTDIR") return [];
    throw error;
  }
  if (!rootStats.isDirectory() || rootStats.isSymbolicLink()) return [];
  const candidates = [];
  const pending = [root];
  while (pending.length > 0) {
    const directory = pending.pop();
    let entries;
    try {
      entries = await readdir(directory, { withFileTypes: true });
    } catch (error) {
      const code = error.code;
      if (code === "ENOENT" || code === "ENOTDIR") continue;
      throw error;
    }
    for (const entry of entries) {
      const path = resolve(directory, entry.name);
      if (entry.isDirectory()) {
        pending.push(path);
      } else if (entry.isFile() && filenameMatchesThread(path, threadId)) {
        candidates.push(path);
      }
    }
  }
  return candidates.sort();
}
async function discoverCodexRolloutByThreadId(input) {
  validateThreadId(input.expectedThreadId);
  const codexHome = resolve(input.codexHome);
  const filenameCandidates = [];
  for (const subdirectory of ROLLOUT_SUBDIRECTORIES) {
    filenameCandidates.push(...await findFilenameCandidates(resolve(codexHome, subdirectory), input.expectedThreadId));
  }
  const validated = [];
  for (const candidate of filenameCandidates) {
    const metadata = await readSessionMeta(candidate, input.expectedThreadId);
    if (metadata && filenameMatchesThread(candidate, input.expectedThreadId)) validated.push(metadata);
  }
  const state = validated.length === 1 ? "found" : validated.length > 1 ? "ambiguous" : filenameCandidates.length > 0 ? "identity_unverified" : "not_found";
  const found = state === "found" ? validated[0] : null;
  return {
    state,
    threadId: input.expectedThreadId,
    codexHome,
    filenameCandidateCount: filenameCandidates.length,
    validatedFileCount: validated.length,
    sourceFile: found?.sourceFile ?? null,
    sourceFileId: found?.sourceFileId ?? null,
    identity: found?.identity ?? null,
    sessionId: found?.sessionId ?? null,
    parentThreadId: found?.parentThreadId ?? null,
    threadSource: found?.threadSource ?? null,
    originator: found?.originator ?? null,
    provider: found?.provider ?? null,
    cliVersion: found?.cliVersion ?? null
  };
}
function snapshotFingerprint(snapshot) {
  return JSON.stringify({
    total: snapshot.total,
    last: snapshot.last,
    modelContextWindow: snapshot.modelContextWindow
  });
}
function parseTailLine(line, threadId, eventOrder, lineNumber) {
  let record;
  try {
    record = JSON.parse(line);
  } catch {
    return null;
  }
  if (record.type === "compacted") {
    return { tokenCount: false, emptyUsage: false, compaction: true, snapshot: null };
  }
  const payload = record.payload && typeof record.payload === "object" && !Array.isArray(record.payload) ? record.payload : null;
  if (record.type !== "event_msg" || payload?.type !== "token_count") {
    return { tokenCount: false, emptyUsage: false, compaction: false, snapshot: null };
  }
  const info = payload.info && typeof payload.info === "object" && !Array.isArray(payload.info) ? payload.info : null;
  if (!info) {
    return { tokenCount: true, emptyUsage: true, compaction: false, snapshot: null };
  }
  const total = usage(info.total_token_usage);
  if (!total || total.totalTokens === null) {
    return { tokenCount: true, emptyUsage: true, compaction: false, snapshot: null };
  }
  return {
    tokenCount: true,
    emptyUsage: false,
    compaction: false,
    snapshot: {
      threadId,
      turnId: null,
      total,
      last: usage(info.last_token_usage),
      modelContextWindow: numeric(info.model_context_window),
      observedAt: typeof record.timestamp === "string" ? record.timestamp : null,
      eventOrder,
      lineNumber,
      source: "codex_rollout_token_count",
      absoluteSnapshot: true
    }
  };
}
var CodexRolloutTailReader = class _CodexRolloutTailReader {
  constructor(codexHome, rolloutFile, expectedThreadId, identity, chunkSize = 64 * 1024) {
    this.codexHome = codexHome;
    this.rolloutFile = rolloutFile;
    this.expectedThreadId = expectedThreadId;
    this.chunkSize = chunkSize;
    this.fileIdentity = identity;
    this.sourceFileId = fileId(rolloutFile);
  }
  codexHome;
  rolloutFile;
  expectedThreadId;
  chunkSize;
  pending = Buffer.alloc(0);
  offset = 0;
  lineCount = 0;
  tokenCountEventCount = 0;
  lastFingerprint = null;
  lastValidSnapshot = null;
  fileIdentity;
  tailBoundaryFingerprint = null;
  initialized = false;
  compactionPending = false;
  sourceFileId;
  static async open(input) {
    validateThreadId(input.expectedThreadId);
    const codexHome = resolve(input.codexHome);
    const rolloutFile = resolve(input.rolloutFile);
    if (!ROLLOUT_SUBDIRECTORIES.some((subdirectory) => isWithin(resolve(codexHome, subdirectory), rolloutFile))) {
      throw new Error("rollout_file_outside_codex_home_sessions");
    }
    if (!filenameMatchesThread(rolloutFile, input.expectedThreadId)) {
      throw new Error("thread_identity_unverified");
    }
    const metadata = await readSessionMeta(rolloutFile, input.expectedThreadId);
    if (!metadata) throw new Error("thread_identity_unverified");
    if (input.chunkSize !== void 0 && (!Number.isSafeInteger(input.chunkSize) || input.chunkSize <= 0)) {
      throw new Error("invalid_chunk_size");
    }
    return new _CodexRolloutTailReader(
      codexHome,
      rolloutFile,
      input.expectedThreadId,
      metadata.identity,
      input.chunkSize
    );
  }
  state() {
    return {
      threadId: this.expectedThreadId,
      sourceFile: this.rolloutFile,
      sourceFileId: this.sourceFileId,
      fileIdentity: this.fileIdentity,
      offset: this.offset,
      pendingBytes: this.pending.length,
      lastValidSnapshot: this.lastValidSnapshot
    };
  }
  reset(identity) {
    this.pending = Buffer.alloc(0);
    this.offset = 0;
    this.lineCount = 0;
    this.tokenCountEventCount = 0;
    this.lastFingerprint = null;
    this.lastValidSnapshot = null;
    this.tailBoundaryFingerprint = null;
    this.compactionPending = false;
    this.fileIdentity = identity;
  }
  processCompleteLines() {
    let updated = null;
    let newTokenCountEventCount = 0;
    let duplicateSnapshotCount = 0;
    let emptyUsageEventCount = 0;
    let invalidJsonLineCount = 0;
    let compactionMarkerCount = 0;
    let observedAfterCompaction = false;
    let newline = this.pending.indexOf(10);
    while (newline >= 0) {
      const lineBytes = this.pending.subarray(0, newline);
      this.pending = this.pending.subarray(newline + 1);
      const line = lineBytes.toString("utf8");
      this.lineCount += 1;
      const parsed = parseTailLine(line, this.expectedThreadId, this.tokenCountEventCount + 1, this.lineCount);
      if (!parsed) {
        invalidJsonLineCount += 1;
      } else {
        if (parsed.compaction) {
          compactionMarkerCount += 1;
          this.compactionPending = true;
        }
        if (parsed.tokenCount) {
          this.tokenCountEventCount += 1;
          newTokenCountEventCount += 1;
        }
        if (parsed.emptyUsage) emptyUsageEventCount += 1;
        if (parsed.snapshot) {
          const fingerprint = snapshotFingerprint(parsed.snapshot);
          if (fingerprint === this.lastFingerprint) {
            duplicateSnapshotCount += 1;
          } else {
            this.lastFingerprint = fingerprint;
            this.lastValidSnapshot = parsed.snapshot;
            updated = parsed.snapshot;
            observedAfterCompaction = this.compactionPending;
            this.compactionPending = false;
          }
        }
      }
      newline = this.pending.indexOf(10);
    }
    return {
      updated,
      newTokenCountEventCount,
      duplicateSnapshotCount,
      emptyUsageEventCount,
      invalidJsonLineCount,
      compactionMarkerCount,
      observedAfterCompaction
    };
  }
  async poll() {
    let pathBefore;
    try {
      pathBefore = await lstat(this.rolloutFile);
    } catch (error) {
      const code = error.code;
      if (code !== "ENOENT" && code !== "ENOTDIR") throw error;
      return this.result("file_changed", null, null, 0, {
        newTokenCountEventCount: 0,
        duplicateSnapshotCount: 0,
        emptyUsageEventCount: 0,
        invalidJsonLineCount: 0,
        compactionMarkerCount: 0,
        observedAfterCompaction: false
      });
    }
    if (!pathBefore.isFile() || pathBefore.isSymbolicLink()) {
      return this.result("identity_unverified", null, null, 0, {
        newTokenCountEventCount: 0,
        duplicateSnapshotCount: 0,
        emptyUsageEventCount: 0,
        invalidJsonLineCount: 0,
        compactionMarkerCount: 0,
        observedAfterCompaction: false
      });
    }
    const identityBefore = fileIdentity(pathBefore);
    let resetReason = !this.initialized ? "initial" : !sameFileIdentity(this.fileIdentity, identityBefore) ? "replaced" : pathBefore.size < this.offset ? "truncated" : null;
    if (!resetReason && this.offset > 0) {
      const currentBoundary = await boundaryFingerprint(this.rolloutFile, this.offset);
      if (currentBoundary !== null && currentBoundary !== this.tailBoundaryFingerprint) {
        resetReason = "truncated";
      }
    }
    if (resetReason) {
      const metadata = await readSessionMeta(this.rolloutFile, this.expectedThreadId);
      if (!metadata || !sameFileIdentity(metadata.identity, identityBefore)) {
        this.reset(identityBefore);
        this.initialized = false;
        return this.result("identity_unverified", resetReason, null, 0, {
          newTokenCountEventCount: 0,
          duplicateSnapshotCount: 0,
          emptyUsageEventCount: 0,
          invalidJsonLineCount: 0,
          compactionMarkerCount: 0,
          observedAfterCompaction: false
        });
      }
      this.reset(identityBefore);
    }
    let handle;
    try {
      handle = await open(this.rolloutFile, "r");
    } catch (error) {
      const code = error.code;
      if (code !== "ENOENT" && code !== "ENOTDIR") throw error;
      return this.result("file_changed", resetReason, null, 0, {
        newTokenCountEventCount: 0,
        duplicateSnapshotCount: 0,
        emptyUsageEventCount: 0,
        invalidJsonLineCount: 0,
        compactionMarkerCount: 0,
        observedAfterCompaction: false
      });
    }
    let bytesRead = 0;
    let bytes = Buffer.alloc(0);
    let fileChangedDuringRead = false;
    let nextBoundaryFingerprint = null;
    try {
      const openBefore = await handle.stat();
      if (!sameFileIdentity(fileIdentity(openBefore), identityBefore)) {
        fileChangedDuringRead = true;
      } else {
        const target = openBefore.size;
        const chunks = [];
        let position = this.offset;
        while (position < target && !fileChangedDuringRead) {
          const length = Math.min(this.chunkSize, target - position);
          const chunk = Buffer.allocUnsafe(length);
          const read = await handle.read(chunk, 0, length, position);
          if (read.bytesRead === 0) break;
          chunks.push(chunk.subarray(0, read.bytesRead));
          position += read.bytesRead;
          bytesRead += read.bytesRead;
        }
        bytes = Buffer.concat(chunks, bytesRead);
        const openAfter = await handle.stat();
        let pathAfter;
        try {
          pathAfter = await lstat(this.rolloutFile);
        } catch (error) {
          const code = error.code;
          if (code !== "ENOENT" && code !== "ENOTDIR") throw error;
          fileChangedDuringRead = true;
        }
        if (pathAfter && (!sameFileIdentity(fileIdentity(openAfter), identityBefore) || !sameFileIdentity(fileIdentity(pathAfter), identityBefore) || !pathAfter.isFile() || pathAfter.isSymbolicLink() || openAfter.size < target || pathAfter.size < target)) {
          fileChangedDuringRead = true;
        }
        if (!fileChangedDuringRead && this.offset > 0) {
          const oldBoundaryAfterRead = await boundaryFingerprint(this.rolloutFile, this.offset);
          if (oldBoundaryAfterRead !== this.tailBoundaryFingerprint) {
            fileChangedDuringRead = true;
          }
        }
        if (!fileChangedDuringRead) {
          const nextOffset = this.offset + bytesRead;
          nextBoundaryFingerprint = await boundaryFingerprint(this.rolloutFile, nextOffset);
          if (nextOffset > 0 && nextBoundaryFingerprint === null) {
            fileChangedDuringRead = true;
          }
        }
      }
    } finally {
      await handle.close();
    }
    if (fileChangedDuringRead) {
      return this.result("file_changed", resetReason, null, 0, {
        newTokenCountEventCount: 0,
        duplicateSnapshotCount: 0,
        emptyUsageEventCount: 0,
        invalidJsonLineCount: 0,
        compactionMarkerCount: 0,
        observedAfterCompaction: false
      });
    }
    this.offset += bytesRead;
    this.tailBoundaryFingerprint = nextBoundaryFingerprint;
    this.pending = this.pending.length === 0 ? bytes : Buffer.concat([this.pending, bytes]);
    const processed = this.processCompleteLines();
    this.initialized = true;
    const status = processed.updated ? "updated" : processed.compactionMarkerCount > 0 ? "compaction_observed" : processed.duplicateSnapshotCount > 0 ? "unchanged" : this.pending.length > 0 ? "partial_line" : this.tokenCountEventCount === 0 ? "no_token_usage" : "unchanged";
    return this.result(status, resetReason, processed.updated, bytesRead, processed);
  }
  result(status, resetReason, snapshot, bytesRead, processed) {
    return {
      status,
      resetReason,
      snapshot,
      state: this.state(),
      bytesRead,
      ...processed
    };
  }
};

// src/observability/codex-master-token-usage.ts
function safeInteger(value) {
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}
function unavailable(status, input) {
  return {
    status,
    source: "codex_rollout",
    threadId: input.threadId,
    threadIdSource: input.threadIdSource,
    codexHomeSource: input.codexHomeSource,
    readMode: null,
    tailStatus: null,
    resetReason: null,
    total: null,
    last: null,
    modelContextWindow: null,
    observedAt: null,
    baselineTotalTokens: input.baselineTotalTokens,
    reportWindowTotalTokens: null,
    reportWindowBasis: null,
    detail: input.detail ?? null
  };
}
var CodexMasterTokenUsageSource = class {
  env;
  codexHome;
  codexHomeSource;
  maxReaders;
  readers = /* @__PURE__ */ new Map();
  constructor(options = {}) {
    this.env = options.env ?? process.env;
    const explicitHome = options.codexHome?.trim();
    const environmentHome = this.env["CODEX_HOME"]?.trim();
    if (explicitHome) {
      this.codexHome = resolve2(explicitHome);
      this.codexHomeSource = "explicit_argument";
    } else if (environmentHome && isAbsolute2(environmentHome)) {
      this.codexHome = resolve2(environmentHome);
      this.codexHomeSource = "codex_environment";
    } else {
      this.codexHome = resolve2(homedir(), ".codex");
      this.codexHomeSource = "default_user_profile";
    }
    const maxReaders = options.maxReaders ?? 8;
    if (!Number.isSafeInteger(maxReaders) || maxReaders < 1 || maxReaders > 32) {
      throw new Error("max_readers_out_of_range");
    }
    this.maxReaders = maxReaders;
  }
  threadId(input) {
    if (Object.hasOwn(input, "threadId")) {
      const explicit = input.threadId?.trim() ?? "";
      return { threadId: explicit || null, threadIdSource: "explicit_argument" };
    }
    const fromCodex = this.env["CODEX_THREAD_ID"]?.trim() ?? "";
    return {
      threadId: fromCodex || null,
      threadIdSource: fromCodex ? "codex_environment" : null
    };
  }
  cache(threadId, reader) {
    this.readers.delete(threadId);
    this.readers.set(threadId, reader);
    while (this.readers.size > this.maxReaders) {
      const oldest = this.readers.keys().next().value;
      if (!oldest) break;
      this.readers.delete(oldest);
    }
  }
  async query(input = {}) {
    const resolvedThread = this.threadId(input);
    const baselineTotalTokens2 = safeInteger(input.baselineTotalTokens);
    if (!resolvedThread.threadId) {
      return unavailable("thread_id_missing", {
        ...resolvedThread,
        codexHomeSource: this.codexHomeSource,
        baselineTotalTokens: baselineTotalTokens2,
        detail: "CODEX_THREAD_ID \u672A\u8BBE\u7F6E\uFF1B\u4E0D\u4F1A\u626B\u63CF\u6216\u731C\u6D4B\u5F53\u524D\u6D3B\u52A8 Thread"
      });
    }
    const threadId = resolvedThread.threadId;
    let reader = this.readers.get(threadId) ?? null;
    const readMode = reader ? "incremental" : "initial";
    if (!reader) {
      let discovery;
      try {
        discovery = await discoverCodexRolloutByThreadId({
          codexHome: this.codexHome,
          expectedThreadId: threadId
        });
      } catch (error) {
        if (error instanceof Error && error.message === "invalid_thread_id") {
          return unavailable("thread_identity_unverified", {
            ...resolvedThread,
            codexHomeSource: this.codexHomeSource,
            baselineTotalTokens: baselineTotalTokens2,
            detail: "Thread ID \u683C\u5F0F\u65E0\u6548"
          });
        }
        return unavailable("source_unavailable", {
          ...resolvedThread,
          codexHomeSource: this.codexHomeSource,
          baselineTotalTokens: baselineTotalTokens2,
          detail: error instanceof Error ? error.message : "Rollout discovery failed"
        });
      }
      if (discovery.state !== "found" || !discovery.sourceFile) {
        const status = discovery.state === "not_found" ? "rollout_not_found" : discovery.state === "ambiguous" ? "rollout_ambiguous" : "thread_identity_unverified";
        return unavailable(status, {
          ...resolvedThread,
          codexHomeSource: this.codexHomeSource,
          baselineTotalTokens: baselineTotalTokens2,
          detail: `discovery_state=${discovery.state}`
        });
      }
      try {
        reader = await CodexRolloutTailReader.open({
          codexHome: this.codexHome,
          rolloutFile: discovery.sourceFile,
          expectedThreadId: threadId
        });
      } catch (error) {
        const code = error.code;
        const status = code === "ENOENT" || code === "ENOTDIR" || code === "EACCES" || code === "EPERM" ? "file_changed" : "thread_identity_unverified";
        return unavailable(status, {
          ...resolvedThread,
          codexHomeSource: this.codexHomeSource,
          baselineTotalTokens: baselineTotalTokens2,
          detail: error instanceof Error ? error.message : "Rollout reader could not be opened"
        });
      }
      this.cache(threadId, reader);
    }
    let poll;
    try {
      poll = await reader.poll();
    } catch (error) {
      this.readers.delete(threadId);
      return unavailable("source_unavailable", {
        ...resolvedThread,
        codexHomeSource: this.codexHomeSource,
        baselineTotalTokens: baselineTotalTokens2,
        detail: error instanceof Error ? error.message : "Rollout poll failed"
      });
    }
    if (poll.status === "file_changed") {
      this.readers.delete(threadId);
      return unavailable("file_changed", {
        ...resolvedThread,
        codexHomeSource: this.codexHomeSource,
        baselineTotalTokens: baselineTotalTokens2,
        detail: "Rollout \u6587\u4EF6\u6682\u65F6\u7F3A\u5931\u3001\u66FF\u6362\u6216\u8BFB\u53D6\u671F\u95F4\u53D1\u751F\u53D8\u5316\uFF1B\u4E0B\u4E00\u6B21\u67E5\u8BE2\u4F1A\u91CD\u65B0\u53D1\u73B0"
      });
    }
    if (poll.status === "identity_unverified") {
      this.readers.delete(threadId);
      return unavailable("thread_identity_unverified", {
        ...resolvedThread,
        codexHomeSource: this.codexHomeSource,
        baselineTotalTokens: baselineTotalTokens2,
        detail: "Rollout \u6587\u4EF6\u540D\u6216 session_meta \u8EAB\u4EFD\u4E0E\u663E\u5F0F Thread ID \u4E0D\u4E00\u81F4"
      });
    }
    const snapshot = poll.state.lastValidSnapshot;
    if (!snapshot || snapshot.threadId !== threadId) {
      this.readers.delete(threadId);
      return unavailable("no_token_count", {
        ...resolvedThread,
        codexHomeSource: this.codexHomeSource,
        baselineTotalTokens: baselineTotalTokens2,
        detail: "Rollout \u4E2D\u5C1A\u65E0\u6709\u6548\u4E14\u8EAB\u4EFD\u5339\u914D\u7684 TokenCount"
      });
    }
    const currentTotal = snapshot.total?.totalTokens ?? null;
    const reportWindowTotalTokens = baselineTotalTokens2 !== null && currentTotal !== null && currentTotal >= baselineTotalTokens2 ? currentTotal - baselineTotalTokens2 : null;
    return {
      status: "ok",
      source: "codex_rollout",
      threadId,
      threadIdSource: resolvedThread.threadIdSource,
      codexHomeSource: this.codexHomeSource,
      readMode,
      tailStatus: poll.status,
      resetReason: poll.resetReason,
      total: snapshot.total,
      last: snapshot.last,
      modelContextWindow: snapshot.modelContextWindow,
      observedAt: snapshot.observedAt,
      baselineTotalTokens: baselineTotalTokens2,
      reportWindowTotalTokens,
      reportWindowBasis: reportWindowTotalTokens === null ? null : "absolute_total_delta",
      detail: poll.state.pendingBytes > 0 ? `tail_pending_bytes=${poll.state.pendingBytes}` : null
    };
  }
};

// src/feedback/template.ts
var NOT_REPORTED = "\u672A\u62A5\u544A";
function formatTokens(value) {
  if (value === null || value === void 0 || !Number.isFinite(value)) return NOT_REPORTED;
  return value.toLocaleString("en-US");
}

// src/feedback/codex-master-token.ts
function codexMasterTokenFeedback(result2) {
  if (result2.status !== "ok") {
    return {
      state: "unavailable",
      note: "\u672A\u53D6\u5F97"
    };
  }
  if (result2.reportWindowTotalTokens === null || result2.reportWindowBasis !== "absolute_total_delta") {
    return {
      state: "unavailable",
      note: "\u672A\u53D6\u5F97"
    };
  }
  return {
    state: "reported",
    note: formatTokens(result2.reportWindowTotalTokens)
  };
}

// src/observability/codex-master-token-cli.ts
function option(name) {
  const index = process.argv.indexOf(name);
  if (index < 0) return null;
  const value = process.argv[index + 1];
  if (!value) throw new Error(`${name}_requires_value`);
  return value;
}
function parseBaseline() {
  const value = option("--baseline-total");
  if (value === null) return null;
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < 0) throw new Error("baseline_total_invalid");
  return parsed;
}
function threadRef(threadId) {
  return threadId ? `thread#${createHash2("sha256").update(threadId).digest("hex").slice(0, 12)}` : null;
}
var explicitThreadId = option("--thread-id");
var baselineTotalTokens = parseBaseline();
var source = new CodexMasterTokenUsageSource();
var result = await source.query({
  ...explicitThreadId === null ? {} : { threadId: explicitThreadId },
  ...baselineTotalTokens === null ? {} : { baselineTotalTokens }
});
process.stdout.write(`${JSON.stringify({
  query: {
    status: result.status,
    source: result.source,
    thread_ref: threadRef(result.threadId),
    thread_id_source: result.threadIdSource,
    codex_home_source: result.codexHomeSource,
    read_mode: result.readMode,
    tail_status: result.tailStatus,
    reset_reason: result.resetReason,
    total: result.total,
    last: result.last,
    model_context_window: result.modelContextWindow,
    observed_at: result.observedAt,
    baseline_total_tokens: result.baselineTotalTokens,
    report_window_total_tokens: result.reportWindowTotalTokens,
    report_window_basis: result.reportWindowBasis,
    detail: result.detail
  },
  feedback_codex_tokens: codexMasterTokenFeedback(result)
}, null, 2)}
`);
