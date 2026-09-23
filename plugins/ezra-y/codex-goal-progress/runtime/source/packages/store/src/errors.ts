export type GoalProgressStoreErrorCode =
  | "HELPER_ALREADY_RUNNING"
  | "HELPER_LOCK_INVALID"
  | "STORE_PATH_INVALID"
  | "STORE_CONTRACT_INVALID"
  | "STORE_COMMAND_INVALID"
  | "STORE_NOT_INITIALIZED"
  | "STORE_ALREADY_INITIALIZED"
  | "EVENT_LOG_CORRUPT"
  | "EVENT_LOG_MISSING"
  | "EVENT_ID_CONFLICT"
  | "REQUEST_ID_CONFLICT"
  | "SNAPSHOT_WRITE_FAILED_AFTER_COMMIT"
  | "STORE_IO_FAILED";

export class GoalProgressStoreError extends Error {
  readonly code: GoalProgressStoreErrorCode;
  readonly committedRevision: number | undefined;

  constructor(
    code: GoalProgressStoreErrorCode,
    message: string,
    options: {
      readonly cause?: unknown;
      readonly committedRevision?: number;
    } = {},
  ) {
    super(message, options.cause === undefined ? undefined : { cause: options.cause });
    this.name = "GoalProgressStoreError";
    this.code = code;
    this.committedRevision = options.committedRevision;
  }
}
