import * as fs from 'node:fs';
import * as path from 'node:path';

export function pathExists(filePath: string): boolean {
  return fs.existsSync(filePath);
}

export function readTextFile(filePath: string): string {
  return fs.readFileSync(filePath, 'utf8');
}

export function readJsonFile<T>(filePath: string): T {
  return JSON.parse(readTextFile(filePath)) as T;
}

export function writeJsonFile(filePath: string, data: unknown): void {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n', 'utf8');
}

export function ensureDir(dirPath: string): void {
  fs.mkdirSync(dirPath, { recursive: true });
}

export function copyDirectory(src: string, dest: string, exclude: string[] = []): void {
  ensureDir(dest);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (exclude.includes(entry.name)) continue;
    const sourcePath = path.join(src, entry.name);
    const destinationPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirectory(sourcePath, destinationPath, exclude);
    } else {
      fs.copyFileSync(sourcePath, destinationPath);
    }
  }
}

/** 文件末尾是崩溃残留的半行（非换行结尾）时，新记录前需补一个换行封口。 */
function needsLeadingNewline(fd: number): boolean {
  const { size } = fs.fstatSync(fd);
  if (size === 0) return false;
  const tail = Buffer.alloc(1);
  fs.readSync(fd, tail, 0, 1, size - 1);
  return tail[0] !== 0x0a;
}

/**
 * 原子追加一行到 append-only 日志（如 events.jsonl）。
 *
 * 用 O_APPEND 打开：内核保证每次 write 定位到当前文件末尾，多个写入者不会互相
 * 覆盖。写完 fsync 落盘再关闭，使「事件已记录」在崩溃后仍成立——这是事件溯源
 * 真相源的最低要求。line 不含结尾换行时自动补上。
 *
 * 崩溃残留处理：进程在追加中途被杀会留下一条无结尾换行的半行。若直接追加，新记录
 * 会与半行粘成一条损坏行，该记录随即丢失。因此追加前检查末字节，必要时把封口换行
 * **并入同一次 write**——单次 write 是 O_APPEND 下唯一的原子单位，既不会与其他
 * 写入者交错，也不需要 ftruncate（截断是非原子的读-改-写，会删掉其他进程已 fsync
 * 的记录，且在 Windows 上 O_APPEND 句柄没有 FILE_WRITE_DATA 会直接失败）。
 * 残留半行原样保留，由读取端记为损坏行——只跳过，绝不删除。
 */
export function appendLineSync(filePath: string, line: string): void {
  const body = line.endsWith('\n') ? line : `${line}\n`;
  // 'a+' 而非 'a'：需要读末字节判断是否封口。只读不截断，故 Windows 同样适用。
  const fd = fs.openSync(filePath, 'a+');
  try {
    fs.writeSync(fd, needsLeadingNewline(fd) ? `\n${body}` : body);
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
}

export interface CorruptLine {
  /** 1 起算的行号，便于定位。 */
  line: number;
  text: string;
}

export interface JsonlReadResult<T> {
  records: T[];
  /** 无法解析的行（正常为空数组）。用于告警，不影响已解析的记录。 */
  corruptLines: CorruptLine[];
}

/**
 * 读取 JSONL 文件，跳过并报告无法解析的行。
 *
 * 损坏行只跳过、不中断：崩溃残留的半行被封口后会停留在文件**中间**，若按「非末行
 * 损坏即抛错」处理，一次崩溃就会让整个事件流永久不可读——那正是本模块要避免的故障。
 * 事件流没有完整性校验链，改动任意一条合法 JSON 都无法察觉，所以抛错并不能真正拦住
 * 篡改，只会把普通崩溃变成事故。损坏行通过 corruptLines 上报，由 `boss doctor` 与
 * 状态物化时的 stderr 告警呈现。
 */
export function readJsonlTolerant<T = unknown>(filePath: string): JsonlReadResult<T> {
  const raw = fs.readFileSync(filePath, 'utf8');
  const records: T[] = [];
  const corruptLines: CorruptLine[] = [];

  const lines = raw.split('\n');
  for (let index = 0; index < lines.length; index += 1) {
    const text = lines[index]!;
    if (text.length === 0) continue;
    try {
      records.push(JSON.parse(text) as T);
    } catch {
      corruptLines.push({ line: index + 1, text });
    }
  }
  return { records, corruptLines };
}
