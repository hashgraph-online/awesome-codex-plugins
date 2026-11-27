// Read complete JSONL records up to the size observed by the caller. An incomplete last line is retried on append.
// Memory for plain transcripts scales with the longest record, including when an old transcript is opened cold.
import { closeSync, openSync, readSync } from "node:fs";

export type VisitLine = (line: Buffer, offset: number) => void;

export function readLines(file: string, start: number, end: number, visit: VisitLine): number {
  if (start >= end) return start;
  const fd = openSync(file, "r");
  try {
    const buffer = Buffer.allocUnsafe(Math.min(end - start, 256 * 1024));
    let pieces: Buffer[] = [];
    let offset = start;
    for (let position = start; position < end;) {
      const read = readSync(fd, buffer, 0, Math.min(buffer.length, end - position), position);
      if (!read) break;
      const chunk = buffer.subarray(0, read);
      let from = 0;
      for (let newline = chunk.indexOf(10); newline >= 0; newline = chunk.indexOf(10, from)) {
        const last = chunk.subarray(from, newline);
        visit(pieces.length ? Buffer.concat([...pieces, last]) : last, offset);
        pieces = [];
        from = newline + 1;
        offset = position + from;
      }
      if (from < read) pieces.push(Buffer.from(chunk.subarray(from)));
      position += read;
    }
    return offset;
  } finally { closeSync(fd); }
}

export function readRecord(file: string, offset: number, length: number): Record<string, any> {
  const fd = openSync(file, "r");
  try {
    const buffer = Buffer.allocUnsafe(length);
    for (let read = 0; read < length;) {
      const count = readSync(fd, buffer, read, length - read, offset + read);
      if (!count) throw new Error("incomplete transcript record");
      read += count;
    }
    return JSON.parse(buffer.toString("utf8"));
  } finally { closeSync(fd); }
}
