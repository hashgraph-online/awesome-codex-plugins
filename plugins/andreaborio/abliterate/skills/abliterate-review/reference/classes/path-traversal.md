# Path traversal and unsafe file access (CWE-22, CWE-73)

## Sources
- Filename/path params (`?file=`, `/download/:name`, wildcard routes `*`), JSON fields naming a file, `Content-Disposition` filename on upload, archive entry names (zip/tar/jar), template or include names, `Referer`-built paths, stored filenames reused later.
- Symlinks and hardlinks inside uploaded archives or user-writable directories.
- Values percent-decoded by the framework after the check, or decoded twice.

## Sinks
| Stack | Sink API | Safe alternative |
| --- | --- | --- |
| Node | `fs.readFile/createReadStream(path.join(base, x))`, `res.sendFile(x)`, `express.static` with user dir, `fs.writeFile`, `unzipper`/`adm-zip`/`tar.extract` | resolve + prefix check (below); `res.sendFile(rel, {root: base})`; store by generated id |
| Python | `open(os.path.join(base, x))`, `send_file(x)`, `send_from_directory` (safe), `zipfile.extractall`, `tarfile.extractall` | `werkzeug.utils.safe_join`, `Path.resolve().is_relative_to(base)`, `tarfile` `filter='data'` where available, per-member check |
| Java | `new File(base, x)`, `Paths.get(base, x)`, `ZipEntry.getName()` into `new File` | `normalize()` then `startsWith(base.toRealPath())`; reject entries outside |
| Go | `filepath.Join(base, x)` + `os.Open`, `http.ServeFile(w, r, x)`, `http.Dir` | `filepath.Clean("/"+x)` joined to base; `filepath.IsLocal`; `os.Root` (`OpenRoot`) when available; `http.FS` with `fs.ValidPath` |
| Ruby / Rails | `send_file params[:f]`, `File.read(File.join(dir, x))`, `render file:`, `render template: params[:t]` | `File.expand_path` + `start_with?(dir + File::SEPARATOR)`; id-based lookup |
| PHP | `file_get_contents($base.$x)`, `include $x`, `readfile`, `ZipArchive::extractTo` | `realpath()` + prefix with trailing separator; basename for flat dirs |
| Any | Archive extraction | check every member's resolved destination stays inside the target; skip symlink/hardlink members or resolve them |

## Guards that work / Look-alike guards
Work:
- Canonicalize the final path (`resolve`/`realpath`/`toRealPath`, which also follows symlinks) and require that it equals base or starts with `base + separator`.
- Generate the on-disk name server-side (uuid) and keep the user's name only as metadata.
- Allowlist lookup (id to path from a table).
- Serving from a dedicated directory with no symlinks that users can create; opening via a directory handle/rooted API.
- For archives: per-entry destination check before writing, plus size/count limits.

Look-alike:
- `startsWith(base)` without the trailing separator (`/srv/uploads` matches `/srv/uploads-private`).
- `path.join`/`os.path.join` alone (`os.path.join(base, "/etc/x")` discards base in Python; `path.resolve` same in Node when second arg is absolute).
- `replace("../", "")` (non-recursive; `....//` collapses to `../`), blocklisting `..` before percent-decoding, or on one OS separator only (`\` on Windows).
- `path.normalize` without checking the result against base; `normalize` on a relative path leaves a leading `..`.
- Check on the path string, then open follows a symlink (TOCTOU, and symlinks planted via archive).
- Extension check only (`.png`) while the name is traversal-capable; null byte tricks in old runtimes are not a reason to rely on extension.
- Checking the archive file name instead of each entry's name.
- `basename` applied in one branch only.

## Falsify before reporting
1. Does the user value reach the path, or only an id mapped to a server-generated path?
2. Is the final path canonicalized and compared with a separator-aware prefix? Read the comparison, including the case where base lacks a trailing separator.
3. Is the framework already protecting it? `send_from_directory`, `res.sendFile` with `root`, and `http.FileServer` reject `..`; verify the call really uses that mode (for Express, `sendFile` with the `root` option).
4. Archive extraction: does the library sanitize entry names by default in the version pinned? If not provable from lockfile/source, mark `needs-evidence`.
5. Can the attacker influence symlinks in the target tree (own uploads, extracted archives, shared volume)?
6. Confirm: a test with `../secret.txt` (placed outside the base in a temp dir) is refused and the outside file's content is not returned/overwritten.

## Severity cues
- Raises: read of config/credentials/source, write or overwrite (code execution via cron/templates/`authorized_keys`), unauthenticated route, container sharing secrets via mounted volumes.
- Lowers: read limited to a public directory, authenticated admin only, base directory contains nothing sensitive, process runs read-only with no secrets.
- Write primitives (zip slip) outrank read primitives at equal reach.

## Regression test
- Fails before: request `file=../outside.txt` where the test creates `outside.txt` beside the base directory; assert 4xx and body does not contain its content.
- Sibling prefix: create `<base>-private/x.txt`; request `../<base-name>-private/x.txt`; assert denied.
- Archive: build a zip in the test with an entry named `../evil.txt`; extract; assert the file is absent outside the target and extraction raises/skips.
- Symlink: a symlink inside the base pointing outside is not followed.
- Allowed case: nested legitimate path `sub/dir/file.txt` and a filename with spaces and unicode still serve.
