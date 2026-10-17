export function isNotFound(error: unknown): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "ENOENT"
  );
}

export function stableErrorCode(error: unknown): string {
  if (
    error !== null &&
    typeof error === "object" &&
    "code" in error &&
    typeof error.code === "string" &&
    error.code.trim()
  ) {
    return error.code.slice(0, 128);
  }
  return error instanceof Error ? error.message.slice(0, 128) : "HELPER_INSPECTION_FAILED";
}
