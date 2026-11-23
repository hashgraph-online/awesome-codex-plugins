#!/usr/bin/env node
/** Offline SITE bundle build/verify: `pack --dir <abs-dir> --out <abs.zip> [--entry <name>]` | `inspect --zip <abs.zip> [--entry <name>]`; caller curls only on exit 0.
 * Exit 0 verified, manifest printed -> upload | 2 verified, flagged entries -> ask user | 1 failure, partial archive removed -> never upload. */
import { spawn, spawnSync } from 'node:child_process';
import { readdirSync, statSync, lstatSync, existsSync, rmSync, accessSync, constants, readFileSync, realpathSync, mkdtempSync, chmodSync, openSync, closeSync, readSync } from 'node:fs';
import { join, relative, resolve, extname, basename, delimiter, isAbsolute } from 'node:path';
import { tmpdir } from 'node:os';

/** Publishable web assets. Allowlist by design: an unknown extension is dropped, never shipped. */
const ALLOWED_EXT = new Set([
  '.html', '.htm', '.css', '.js', '.mjs', '.cjs', '.json', '.xml', '.webmanifest',
  '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico', '.bmp',
  '.woff', '.woff2', '.ttf', '.otf',
  '.txt', '.md', '.pdf',
  '.mp4', '.webm', '.mp3', '.wav',
  '.tiff', '.csv', '.markdown', '.rst', '.yaml', '.yml', '.toml', '.ini', '.properties', '.conf', '.cfg', '.dockerfile',
  '.zip', '.tar', '.gz', '.7z', '.mov', '.mkv', '.avi', '.ogg', '.m4a', '.aac', '.flac', '.opus', '.weba',
  '.sql', '.log', '.tsv', '.jsx', '.ts', '.tsx', '.docx', '.xlsx', '.pptx', '.docm', '.xlsm', '.pptm', '.doc', '.xls', '.ppt',
  '.odt', '.ods', '.odp', '.glb', '.gltf', '.obj', '.mtl', '.stl', '.ply', '.off', '.fbx', '.dae', '.3mf', '.usdz',
  '.usd', '.usda', '.usdc', '.x3d', '.3ds', '.blend', '.step', '.stp', '.iges', '.igs', '.amf', '.wrl', '.vrml', '.bin',
]);

/** Names that stay out even when the extension is allowed. */
const EXCLUDED_DIRS = new Set(['node_modules', 'vendor', '__pycache__', 'dist-cache', '__MACOSX']);
const PRIVATE_DIR_NAMES = new Set(['.claude', '.codex', '.openclaw', '.ssh', '.aws', '.gnupg']);

/** The one dot-folder a site keeps, at the root only (brewpage.app publishes it, drops other hidden entries). */
const TRUSTED_DOT_DIR = '.well-known';

/** System entries brewpage.app drops on its own: never counted, never flagged. */
const SYSTEM_RE = /^(__MACOSX|\.Spotlight-V100|\.Trashes|\.fseventsd)\/|(^|\/)(\.DS_Store|Thumbs\.db|desktop\.ini)$/i;

/** True when a dot-named segment, outside the root `.well-known/`, keeps the path out of a site. */
const isHidden = (rel) => rel.split('/').some((s, i) => s.startsWith('.') && !(i === 0 && s === TRUSTED_DOT_DIR));

/** Extension-less files ship only inside the root `.well-known/` (e.g. `apple-app-site-association`). */
const isWellKnownBare = (rel) => rel.startsWith(`${TRUSTED_DOT_DIR}/`) && extname(rel) === '';

/** Entries that still need a human OK if they survive the allowlist. */
const SENSITIVE_RE = /(^|\/)(\.env|id_rsa|id_ed25519)|secret|credential|password|token|\.(pem|key|p12|pfx|crt|map)$/i;
const RESERVED_RE = /^(?:\.env(?:\..*)?|\.brewpage-(?:[a-f0-9]{24}|owner.*)|id_(?:rsa|ed25519)|brewpage(?:\.[a-z0-9]{6}|-pack-[a-z0-9]{6}|[-_.]history\.md|[-_.]reconciliation\.json)|\.?(?:brewpage[-_.])?(?:owner[-_]token|credentials?|password(?:[-_]source)?|password[-_]header|recovery(?:[-_]receipt)?)(?:\.(?:md|txt|json|env|key))?|auth\.json|auth-profiles\.json|tokens\.json)$/i;
const reservedMessage = 'reserved credential input; select only publishable files or rebuild the archive without credentials';

function reservedPaths(args) {
  if (args.excluded.some(path => !isAbsolute(path))) die('--exclude-file must name an absolute protected path');
  const paths = [args['history-file'], args['password-file'], args['owner-token-file'], ...args.excluded].filter(Boolean);
  const identities = new Set(paths.filter(existsSync).map(path => {
    const info = statSync(path, { bigint: true });
    return `${info.dev}/${info.ino}`;
  }));
  const names = new Set(paths.map(path => basename(path).toLowerCase()));
  return {
    member: (name) => name.split(/[/\\]/).some(part => RESERVED_RE.test(part.trim()) || names.has(part.trim().toLowerCase())),
    identity: (info) => identities.has(`${info.dev}/${info.ino}`),
  };
}

const ENTRY_RE = /^[A-Za-z0-9._-]+(\/[A-Za-z0-9._-]+)*$/;

/** Bound central-directory metadata and integrity-check output before processing. */
const LIST_MAX_BUFFER = 1024 * 1024;
const CHECK_TIMEOUT_MS = 10000;

// Bind reads to directory descriptors: a source rename must never redirect ZIP reads outside the selected tree.
const SNAPSHOT = String.raw`
import json, os, stat, sys
try:
    os.umask(0o077)
    data = json.load(sys.stdin)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root = os.open('/', flags)
    try:
        for part in data['root'].split('/'):
            if not part:
                continue
            next_fd = os.open(part, flags, dir_fd=root)
            os.close(root)
            root = next_fd
        info = os.fstat(root)
        if [str(info.st_dev), str(info.st_ino)] != [data['dev'], data['ino']]:
            raise ValueError('source root changed')
        total = 0
        if len(data['kept']) > 200:
            raise ValueError('file limit')
        for name, dev, ino in data['kept']:
            parts = name.split('/')
            if any(part in ('', '.', '..') for part in parts) or len(name.encode('utf-8')) > 900:
                raise ValueError('invalid member')
            parent = os.dup(root)
            try:
                for part in parts[:-1]:
                    next_fd = os.open(part, flags, dir_fd=parent)
                    os.close(parent)
                    parent = next_fd
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(fd, 'rb') as source:
                    info = os.fstat(source.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or [str(info.st_dev), str(info.st_ino)] != [dev, ino] or info.st_size > 5 * 1024 * 1024:
                        raise ValueError('invalid source file')
                    target = os.path.join(sys.argv[1], *parts)
                    os.makedirs(os.path.dirname(target), mode=0o700, exist_ok=True)
                    output = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                    with os.fdopen(output, 'wb') as dest:
                        size = 0
                        while True:
                            chunk = source.read(65536)
                            if not chunk:
                                break
                            size += len(chunk)
                            total += len(chunk)
                            if size > 5 * 1024 * 1024 or total > 40 * 1024 * 1024:
                                raise ValueError('byte limit')
                            dest.write(chunk)
                        dest.flush()
                        os.utime(dest.fileno(), ns=(info.st_atime_ns, info.st_mtime_ns))
            finally:
                os.close(parent)
    finally:
        os.close(root)
except (OSError, ValueError, KeyError, AttributeError):
    sys.exit(1)
`;

const FILE_SNAPSHOT = String.raw`
import os, shutil, stat, sys
try:
    source, target, dev, ino, staged = sys.argv[1:]
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open('/', flags)
    for part in source.split('/')[1:-1]:
        next_fd = os.open(part, flags, dir_fd=directory)
        os.close(directory)
        directory = next_fd
    fd = os.open(source.split('/')[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(fd, 'rb') as incoming:
        info = os.fstat(incoming.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or [str(info.st_dev), str(info.st_ino)] != [dev, ino]:
            raise ValueError('selected file changed')
        if staged == 'yes' and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600):
            raise ValueError('staged content must remain private')
        parent = os.fstat(directory)
        if staged == 'yes' and (parent.st_uid != os.getuid() or stat.S_IMODE(parent.st_mode) != 0o700):
            raise ValueError('staged run must remain private')
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        with os.fdopen(os.open(target, flags, 0o600), 'wb') as outgoing:
            shutil.copyfileobj(incoming, outgoing)
except (OSError, ValueError):
    sys.exit(1)
`;

const MCP_FILES = String.raw`
import json, os, sys, zipfile
try:
    with zipfile.ZipFile(sys.argv[1]) as archive:
        files = []
        for entry in sorted(archive.infolist(), key=lambda info: info.filename):
            if entry.is_dir():
                continue
            suffix = os.path.splitext(entry.filename)[1].lower()
            if suffix not in ('.html', '.htm', '.css', '.js', '.mjs', '.cjs', '.json', '.xml', '.webmanifest', '.svg', '.txt', '.md', '.csv', '.markdown', '.rst', '.yaml', '.yml', '.toml', '.ini', '.properties', '.conf', '.cfg', '.dockerfile', '.sql', '.log', '.tsv', '.jsx', '.ts', '.tsx', '.gltf', '.obj', '.mtl', '.stl', '.off', '.dae', '.usd', '.usda', '.x3d', '.step', '.stp', '.iges', '.igs', '.amf', '.wrl', '.vrml', ''):
                sys.exit(2)
            content = archive.read(entry).decode('utf-8')
            if '\x00' in content:
                sys.exit(2)
            files.append({'path': entry.filename, 'content': content})
        fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(files, output, ensure_ascii=False)
except UnicodeError:
    sys.exit(2)
except (OSError, ValueError, zipfile.BadZipFile):
    sys.exit(1)
`;

// Local and central entries must identify the same bounded, unambiguous UTF-8 members.
function archiveMembers(zipPath, reserved) {
  const rejected = why => ({ why });
  if (statSync(zipPath).size > 25 * 1024 * 1024) return rejected('archive exceeds local inspection limits');
  const data = readFileSync(zipPath);
  let end = data.length - 22;
  const floor = Math.max(0, end - 65535);
  while (end >= floor && !(data.readUInt32LE(end) === 0x06054b50 && end + 22 + data.readUInt16LE(end + 20) === data.length)) end--;
  if (end < floor) return rejected('archive has no valid central directory');
  const count = data.readUInt16LE(end + 10);
  const size = data.readUInt32LE(end + 12);
  let position = data.readUInt32LE(end + 16);
  if (data.readUInt16LE(end + 4) || data.readUInt16LE(end + 6) || data.readUInt16LE(end + 8) !== count || count === 65535 || position + size !== end) return rejected('unsupported ZIP64 or split archive');
  if (count > 400 || size > LIST_MAX_BUFFER) return rejected('archive exceeds local inspection limits');
  const centralStart = position;
  const spans = [];
  const paths = new Set();
  const names = [];
  let expanded = 0;
  for (let i = 0; i < count; i++) {
    if (position + 46 > end || data.readUInt32LE(position) !== 0x02014b50) return rejected('archive central directory is malformed');
    const bytes = data.readUInt32LE(position + 24);
    const length = data.readUInt16LE(position + 28);
    const extra = position + 46 + length;
    const extraEnd = extra + data.readUInt16LE(position + 30);
    const next = extraEnd + data.readUInt16LE(position + 32);
    if (next > end || data.readUInt32LE(position + 20) === 0xffffffff || data.readUInt32LE(position + 42) >= end || data.readUInt16LE(position + 34)) return rejected('archive central directory is malformed');
    const nameBytes = data.subarray(position + 46, position + 46 + length);
    const name = nameBytes.toString('utf8');
    const local = data.readUInt32LE(position + 42);
    if (local + 30 + length > end || data.readUInt32LE(local) !== 0x04034b50 || data.readUInt16LE(local + 26) !== length ||
        !nameBytes.equals(data.subarray(local + 30, local + 30 + length))) return rejected('archive member paths disagree');
    if (reserved.member(name)) return rejected(reservedMessage);
    const directory = name.endsWith('/');
    const path = directory ? name.slice(0, -1) : name;
    if (!nameBytes.equals(Buffer.from(name)) || /[\\\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u.test(path) ||
        path.split('/').some(part => part === '' || part !== part.trim() || part === '.' || part.toLowerCase().replace(/%2e/g, '.') === '..') ||
        paths.has(path)) return rejected('archive member paths are ambiguous');
    paths.add(path);
    const flags = data.readUInt16LE(position + 8);
    const compressed = data.readUInt32LE(position + 20);
    const localExtra = local + 30 + length;
    const localExtraEnd = localExtra + data.readUInt16LE(local + 28);
    const payloadEnd = localExtraEnd + compressed;
    if (data.readUInt16LE(local + 6) !== flags || data.readUInt16LE(local + 8) !== data.readUInt16LE(position + 10) || payloadEnd > centralStart) return rejected('archive member headers disagree');
    if (!sameArchiveName(data, extra, extraEnd, nameBytes) || !sameArchiveName(data, localExtra, localExtraEnd, nameBytes)) return rejected('archive member paths disagree');
    let memberEnd = payloadEnd;
    if (flags & 8) {
      if (payloadEnd + 12 > centralStart) return rejected('archive data descriptor is malformed');
      const descriptor = data.readUInt32LE(payloadEnd) === 0x08074b50 ? payloadEnd + 4 : payloadEnd;
      memberEnd = descriptor + 12;
      if (memberEnd > centralStart || !data.subarray(descriptor, memberEnd).equals(data.subarray(position + 16, position + 28))) return rejected('archive data descriptor is malformed');
    } else if (!data.subarray(local + 14, local + 26).equals(data.subarray(position + 16, position + 28))) return rejected('archive member lengths or checksums disagree');
    spans.push([local, memberEnd]);
    expanded += bytes;
    if (!directory) names.push(name);
    if (bytes > 5 * 1024 * 1024 || expanded > 40 * 1024 * 1024 || names.length > 200 || length > 900) return rejected('archive exceeds local inspection limits');
    position = next;
  }
  if (position !== end) return rejected('archive central directory is malformed');
  spans.sort((a, b) => a[0] - b[0]);
  let offset = 0;
  for (const [start, finish] of spans) {
    if (start !== offset) return rejected('archive has unlisted or overlapping member data');
    offset = finish;
  }
  return offset === centralStart ? { names: names.sort() } : rejected('archive has unlisted member data');
}

function sameArchiveName(data, start, end, name) {
  for (let offset = start; offset < end;) {
    if (offset + 4 > end) return false;
    const tag = data.readUInt16LE(offset);
    const length = data.readUInt16LE(offset + 2);
    const next = offset + 4 + length;
    if (next > end) return false;
    if (tag === 0x7075 && (length < 5 || data[offset + 4] !== 1 || !data.subarray(offset + 9, next).equals(name))) return false;
    offset = next;
  }
  return true;
}

function die(msg) {
  console.log(`FAILED: ${msg}`);
  console.log('RESULT: fail');
  process.exit(1);
}

function parseArgs(argv) {
  const out = { mode: argv[0], excluded: [] };
  for (let i = 1; i < argv.length; i += 2) {
    const k = argv[i];
    const v = argv[i + 1];
    if (!k.startsWith('--') || v === undefined) die(`bad argument near "${k}"`);
    if (k === '--exclude-file') out.excluded.push(v);
    else out[k.slice(2)] = v;
  }
  return out;
}

function validateEntry(entry) {
  if (entry === undefined) return undefined;
  if (!ENTRY_RE.test(entry) || entry.split('/').includes('..')) {
    die(`entry "${entry}" is not a plain relative file name`);
  }
  return entry;
}

/** Recursively collect allowlisted regular files, relative to root, sorted. */
function collect(root, reserved) {
  const kept = [];
  const skipped = [];
  let protectedSkipped = 0;
  const identified = new Map();
  const walk = (dir) => {
    for (const name of readdirSync(dir).sort()) {
      const abs = join(dir, name);
      const rel = relative(root, abs);
      const st = lstatSync(abs, { bigint: true });
      const trusted = dir === root && name === TRUSTED_DOT_DIR && st.isDirectory();
      if (reserved.member(name) || reserved.identity(st) || PRIVATE_DIR_NAMES.has(name.toLowerCase())) { protectedSkipped++; continue; }
      if ((name.startsWith('.') && !trusted) || EXCLUDED_DIRS.has(name)) { skipped.push(rel); continue; }
      if (st.isSymbolicLink()) { skipped.push(rel); continue; }
      if (st.isDirectory()) { walk(abs); continue; }
      if (!st.isFile() || st.nlink !== 1n) { skipped.push(rel); continue; }
      if (!ALLOWED_EXT.has(extname(name).toLowerCase()) && !isWellKnownBare(rel)) { skipped.push(rel); continue; }
      if (/[\r\n]/.test(rel)) { skipped.push(rel); continue; }
      kept.push(rel);
      identified.set(rel, [rel, String(st.dev), String(st.ino)]);
    }
  };
  walk(root);
  return { kept: kept.sort(), skipped: skipped.sort(), protectedSkipped, identified };
}

function resolveEntry(names, requested) {
  if (requested !== undefined) {
    if (!names.includes(requested)) die(`entry "${requested}" is not in the archive`);
    return requested;
  }
  // Server rule: root index.html, else the shallowest HTML file (ties: name order).
  const html = names.filter((n) => !SYSTEM_RE.test(n) && !isHidden(n) && /\.html?$/i.test(n));
  const index = html.find((n) => n.toLowerCase() === 'index.html');
  if (index !== undefined) return index;
  if (html.length === 0) die('no .html file in the bundle — refusing to guess an entry file');
  const depth = (n) => n.split('/').length;
  return [...html].sort((a, b) => depth(a) - depth(b) || (a < b ? -1 : a > b ? 1 : 0))[0];
}

/** True when `p` is an executable regular file. */
function isExecutable(p) {
  try { accessSync(p, constants.X_OK); return statSync(p).isFile(); } catch { return false; }
}

/** Check executable availability through filesystem metadata on PATH. */
function requireTool(bin) {
  const exts = process.platform === 'win32' ? ['', ...(process.env.PATHEXT || '.EXE;.CMD;.BAT').split(';')] : [''];
  const dirs = (process.env.PATH || '').split(delimiter).filter(Boolean);
  if (!dirs.some((dir) => exts.some((ext) => isExecutable(join(dir, bin + ext))))) die(`${bin} required`);
}

// Keep Info-ZIP option defaults out of the fixed archive arguments.
const archiveEnv = { ...process.env };
for (const key of ['ZIP', 'ZIPOPT', 'UNZIP', 'UNZIPOPT', 'ZIPINFO', 'ZIPINFOOPT']) delete archiveEnv[key];

/** Why a spawnSync child failed, '' on success; its own non-zero exit wins over the EPIPE it causes. */
function failure(bin, r) {
  if (r.status !== 0 && r.status !== null) return `${bin} exited ${r.status}`;
  if (r.error) return `${bin} failed (${r.error.code || r.error.message})`;
  return r.signal ? `${bin} killed by ${r.signal}` : '';
}

function checkIntegrity(zipPath) {
  const r = spawnSync('unzip', ['-tq', zipPath], { env: archiveEnv, encoding: 'utf8', maxBuffer: LIST_MAX_BUFFER, timeout: CHECK_TIMEOUT_MS, killSignal: 'SIGKILL' });
  if (r.status !== 0 && r.status !== null) return 'archive failed its integrity check';
  const why = failure('unzip', r);
  return why ? `archive could not be checked: ${why}` : '';
}

function listArchive(zipPath, reserved) {
  const inspected = archiveMembers(zipPath, reserved);
  if (inspected.why) return inspected;
  const why = checkIntegrity(zipPath);
  return why ? { why } : inspected;
}

/** The one manifest format, and the only place the exit code is decided; always the caller's last call.
 * exitCode, never process.exit(): exit drops stdout still queued for a slow pipe reader (manifest > 64 KB). */
function report(names, bytes, entry, skipped, zipPath, unexpected = [], protectedSkipped = 0) {
  console.log(`ARCHIVE MANIFEST — ${basename(zipPath)}`);
  for (const n of names) console.log(`  ${n}`);
  console.log(`FILES: ${names.length}`);
  console.log(`BYTES: ${bytes}`);
  console.log(`ENTRY: ${entry}`);
  const skippedSummary = [...skipped, ...(protectedSkipped ? [`${protectedSkipped} protected credential inputs`] : [])];
  console.log(`SKIPPED: ${skipped.length + protectedSkipped}${skippedSummary.length ? ` (${skippedSummary.join(', ')})` : ''}`);
  if (unexpected.length) console.log(`UNEXPECTED: ${unexpected.join(', ')}`);
  const flagged = names.filter((n) => SENSITIVE_RE.test(n));
  if (flagged.length) console.log(`SENSITIVE: ${flagged.join(', ')}`);
  const confirm = unexpected.length > 0 || flagged.length > 0;
  console.log(`RESULT: ${confirm ? 'confirm' : 'ok'}`);
  process.exitCode = confirm ? 2 : 0;
}

async function pack(args) {
  let dir = args.dir;
  if (!dir || !args.out) die('pack needs --dir and --out');
  const out = resolve(args.out);
  if (!out.endsWith('.zip')) die('--out must end with .zip');
  if (!existsSync(dir) || !statSync(dir).isDirectory()) die(`not a directory: ${dir}`);
  const entryArg = validateEntry(args.entry);
  requireTool('zip');
  requireTool('unzip');
  requireTool('python3');

  dir = realpathSync(dir);
  const rootInfo = statSync(dir, { bigint: true });

  const reserved = reservedPaths(args);
  if (reserved.member(dir)) die(reservedMessage);
  const { kept, skipped, protectedSkipped, identified } = collect(dir, reserved);
  if (kept.length === 0) die(`no publishable files under ${dir} after the allowlist filter`);
  const entry = resolveEntry(kept, entryArg);

  // BD-N03: `mktemp` leaves a 0-byte file that Info-ZIP reads as a corrupt
  // archive and exits 3. Start from no file at all, every time.
  rmSync(out, { force: true });

  let snapshot;
  let active;
  let interrupted;
  const cancel = (signal) => { interrupted ||= signal; active?.stop(signal); };
  const onInt = () => cancel('SIGINT');
  const onTerm = () => cancel('SIGTERM');
  const onHup = () => cancel('SIGHUP');
  process.on('SIGINT', onInt);
  process.on('SIGTERM', onTerm);
  process.on('SIGHUP', onHup);
  // Keep the event loop available for ordinary cancellation; child output is discarded, never retained or printed.
  const run = (bin, argv, options) => new Promise((resolve) => {
    if (interrupted) { resolve({ status: null, signal: interrupted }); return; }
    const child = spawn(bin, argv, { cwd: options.cwd, env: options.env, stdio: ['pipe', 'ignore', 'ignore'] });
    const result = { status: null, signal: null };
    let escalation;
    const stop = (signal) => {
      child.kill(signal);
      escalation ||= setTimeout(() => child.kill('SIGKILL'), 1000);
    };
    active = { stop };
    const timeout = setTimeout(() => { result.error = { code: 'ETIMEDOUT' }; stop('SIGTERM'); }, CHECK_TIMEOUT_MS);
    child.on('error', (error) => { result.error = error; });
    child.stdin.on('error', (error) => { result.error ||= error; });
    child.on('close', (status, signal) => {
      clearTimeout(timeout);
      clearTimeout(escalation);
      active = undefined;
      result.status = status < 0 ? null : status;
      result.signal = signal;
      resolve(result);
    });
    child.stdin.end(options.input);
  });
  let z;
  let snapshotWhy;
  try {
    snapshot = mkdtempSync(join(tmpdir(), 'brewpage-pack-'));
    chmodSync(snapshot, 0o700);
    const copied = await run('python3', ['-I', '-S', '-c', SNAPSHOT, snapshot], {
      input: JSON.stringify({ root: dir, dev: String(rootInfo.dev), ino: String(rootInfo.ino), kept: kept.map(name => identified.get(name)) }), encoding: 'utf8',
    });
    snapshotWhy = failure('python3', copied);
    if (!snapshotWhy) z = await run('zip', ['-q', '-X', '-@', out], {
      cwd: snapshot, env: archiveEnv, input: `${kept.join('\n')}\n`, encoding: 'utf8',
    });
  } finally {
    if (snapshot) rmSync(snapshot, { recursive: true, force: true });
    if (interrupted) rmSync(out, { force: true });
    process.removeListener('SIGINT', onInt);
    process.removeListener('SIGTERM', onTerm);
    process.removeListener('SIGHUP', onHup);
  }
  if (interrupted) die(`pack interrupted (${interrupted})`);
  if (snapshotWhy) { rmSync(out, { force: true }); die('source could not be snapshotted safely'); }
  // zip exiting 0 without reading the list still fails: EPIPE (z.error) with status 0.
  const zipWhy = failure('zip', z);
  if (zipWhy) {
    rmSync(out, { force: true });
    die(`${zipWhy} — no archive produced`);
  }

  if (!existsSync(out) || statSync(out).size === 0) {
    rmSync(out, { force: true });
    die('zip produced no usable archive');
  }
  const bytes = statSync(out).size;
  const { names: listed, why } = listArchive(out, reserved);
  if (why) { rmSync(out, { force: true }); die(why); }
  if (listed.join('\n') !== kept.join('\n')) {
    rmSync(out, { force: true });
    die(`archive contents differ from the selected file set (in archive: ${listed.length}, selected: ${kept.length})`);
  }
  if (args['mcp-out']) {
    const encoded = spawnSync('python3', ['-I', '-S', '-c', MCP_FILES, out, args['mcp-out']], { stdio: 'ignore', timeout: CHECK_TIMEOUT_MS });
    if (encoded.status !== 2 && failure('python3', encoded)) die('could not prepare checked MCP input');
  }
  report(listed, bytes, entry, skipped, out, [], protectedSkipped);
}

function inspect(args) {
  if (!args.zip) die('inspect needs --zip');
  const zipPath = resolve(args.zip);
  if (!existsSync(zipPath) || !statSync(zipPath).isFile()) die(`not a file: ${zipPath}`);
  const entryArg = validateEntry(args.entry);
  requireTool('unzip');

  const bytes = statSync(zipPath).size;
  if (bytes === 0) die('archive is 0 bytes');
  const { names: listed, why } = listArchive(zipPath, reservedPaths(args));
  if (why) die(why);
  if (listed.length === 0) die('archive contains no files');
  const entry = resolveEntry(listed, entryArg);

  // A supplied ZIP is not rewritten: entries outside the allowlist or hidden go to a human decision;
  // system entries the server drops itself are left alone.
  const unexpected = listed.filter((n) => !SYSTEM_RE.test(n) && ((!ALLOWED_EXT.has(extname(n).toLowerCase()) && !isWellKnownBare(n)) || isHidden(n)));
  report(listed, bytes, entry, [], zipPath, unexpected);
}

function file(args) {
  if (!args.path || (!args.out && args['check-only'] !== 'yes')) die('file needs --path and --out');
  const reserved = reservedPaths(args);
  const source = realpathSync(args.path);
  const info = lstatSync(source, { bigint: true });
  const staged = args['staged-content'] === 'yes' && basename(source) === 'brewpage-content.md' && lstatSync(args.path).isFile();
  if (reserved.identity(info) || (!staged && (reserved.member(args.path) || reserved.member(source)))) die(reservedMessage);
  if (!info.isFile() || info.nlink !== 1n) die('select a regular file without hard links');
  if (staged && (info.uid !== BigInt(process.getuid()) || (info.mode & 0o777n) !== 0o600n)) die('staged content must remain private');
  if (args['check-only'] === 'yes') return;
  if (args['zip-snapshot'] === 'yes' && info.size > 25n * 1024n * 1024n) die('archive exceeds local inspection limits');
  const copied = spawnSync('python3', ['-I', '-S', '-c', FILE_SNAPSHOT, source, args.out, String(info.dev), String(info.ino), staged ? 'yes' : 'no'], { stdio: 'ignore', timeout: CHECK_TIMEOUT_MS });
  if (failure('python3', copied)) die('source could not be snapshotted safely');
  const signature = Buffer.alloc(4);
  const fd = openSync(args.out, 'r');
  try { readSync(fd, signature); } finally { closeSync(fd); }
  if (args['zip-snapshot'] === 'yes') return;
  if (signature.equals(Buffer.from('504b0304', 'hex'))) {
    const { why: problem } = archiveMembers(args.out, reserved);
    if (problem) {
      rmSync(args.out, { force: true });
      die(problem);
    }
  }
}

const args = parseArgs(process.argv.slice(2));
try {
  if (args.mode === 'pack') await pack(args);
  else if (args.mode === 'inspect') inspect(args);
  else if (args.mode === 'file') file(args);
  else die('usage: publish.mjs pack --dir <dir> --out <zip> [--entry <name>] | inspect --zip <zip> [--entry <name>]');
} catch {
  die('local source could not be checked safely');
}
