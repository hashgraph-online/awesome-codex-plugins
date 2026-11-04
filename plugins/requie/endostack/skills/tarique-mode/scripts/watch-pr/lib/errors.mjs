// Error types shared by the watcher.

export class UsageError extends Error {
  constructor(message) {
    super(message);
    this.name = 'UsageError';
  }
}

// A failure to read GitHub state. `kind` is one of:
//   command-failed, json-parse, missing-field, unexpected-value,
//   checks-unavailable, invalid-pr-url, context
// `retryable` false means the watcher stops at once with exit 7.
export class QueryError extends Error {
  constructor(kind, detail, { retryable = true, raw } = {}) {
    super(`${kind}: ${detail}`);
    this.name = 'QueryError';
    this.kind = kind;
    this.detail = detail;
    this.retryable = retryable;
    if (raw !== undefined) this.raw = raw;
  }

  toJSON() {
    const out = { kind: this.kind, detail: this.detail, retryable: this.retryable };
    if (this.raw !== undefined) out.raw = this.raw;
    return out;
  }
}

export function firstLine(text, max = 240) {
  const line = String(text ?? '').split(/\r?\n/).find((l) => l.trim() !== '') ?? '';
  return line.trim().slice(0, max);
}

// Turn anything thrown while reading into a QueryError so the retry loop
// only has one shape to handle.
export function asQueryError(err) {
  if (err instanceof QueryError) return err;
  return new QueryError('missing-field', err?.message ?? String(err));
}
