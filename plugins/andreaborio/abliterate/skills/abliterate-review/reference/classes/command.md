# Command, argument and code injection (CWE-78, CWE-88, CWE-94)

## Sources
- HTTP params, filenames from uploads, URLs fetched by the server, Git ref/branch names, repo-controlled files (package.json scripts, Makefile), webhook payloads, image/PDF metadata.
- Values stored earlier and passed to a worker later (conversion jobs, export, backup).
- Attacker-supplied templates, formulas, "expression" or "rule" fields, config uploaded as YAML.
- Strings starting with `-` reaching a CLI argument position (argument injection, CWE-88) even when no shell is involved.

## Sinks
| Language | Sink API | Safe alternative |
| --- | --- | --- |
| Node | `child_process.exec`, `execSync`, `spawn(cmd, {shell:true})` with built string | `execFile`/`spawn` with argv array, `shell:false` |
| Python | `os.system`, `os.popen`, `subprocess.*(..., shell=True)` with f-string, `commands` | `subprocess.run([...], shell=False)`; `shlex.quote` only if a shell is unavoidable |
| Ruby | backticks, `system("..#{x}")`, `%x`, `exec`, `Open3.capture3(str)` | `system("cmd", arg1, arg2)` (multi-arg form) |
| PHP | `exec`, `system`, `shell_exec`, `passthru`, backticks, `popen`, `proc_open(string)` | `proc_open` with array; `escapeshellarg` per argument |
| Go | `exec.Command("sh", "-c", s)`, `exec.Command("bash","-c",...)` | `exec.Command(bin, args...)` |
| Java | `Runtime.exec(String)`, `ProcessBuilder("sh","-c",s)` | `ProcessBuilder(list)` with a fixed binary |
| JS code eval | `eval`, `new Function`, `setTimeout(string)`, `vm.runInNewContext` (not a sandbox), `vm2`-style "sandboxes" | data-only parsing (`JSON.parse`), allowlisted operation table |
| Python code eval | `eval`, `exec`, `compile`, `pickle`, `yaml.load` w/o SafeLoader | `ast.literal_eval`, `yaml.safe_load` |
| Template engines | Jinja2 `Template(user_str)` / `from_string`, Twig/Smarty/Freemarker/Velocity/Thymeleaf with user-controlled template or view name, EJS `render(userStr)`, Handlebars `compile(user)` helpers | Fixed template files; pass user input only as context data; Jinja `SandboxedEnvironment` if user templates are a feature |
| Ruby code eval | `eval`, `instance_eval`, `send(params[:m])`, `constantize` on input, `ERB.new(user)` | allowlist of method/class names |

Argument-position hazards even with argv arrays: `git` (`--upload-pack`, `-c`), `tar` (`--checkpoint-action`), `curl` (`-o`, `@file`), `ssh` (`-o ProxyCommand`), `rsync`, `find -exec`, `convert/magick` (`@file`, `msl:`). Fix: `--` terminator, validate against an allowlist/regex of the full value, reject leading `-`.

## Guards that work / Look-alike guards
Work:
- argv-array execution with a fixed executable and no shell.
- Allowlist of full values (enum of formats, anchored `^[A-Za-z0-9._-]+$` plus rejection of leading `-`) applied right before the call.
- `--` before user positional args when the tool supports it.
- Dedicated library instead of shelling out (zip, image, git bindings).

Look-alike:
- Blocklist of `;`, `|`, `&`, backtick (misses `$()`, newline, redirection, argument flags).
- `shlex.quote`/`escapeshellarg` applied but the result lands in a context not shell-quoted (inside `bash -c` heredoc, after `-o`, in a `-e` script).
- `escapeshellcmd` (not `escapeshellarg`) on a whole command.
- Quote stripping, `replace("..", "")`.
- Frontend regex on the input; trimming/lowercasing.
- "Sandbox" modules for JS/Python eval presented as safe.
- Validating a prefix (`startsWith("img-")`) then passing the entire string.

## Falsify before reporting
1. Is a shell involved? `execFile`/`spawn` without `shell:true`, Go `exec.Command(bin, args...)`, `subprocess` list form: metacharacters are inert. Then only argument injection remains.
2. Is the argument value constrained before it gets here (enum, regex, id looked up in DB, server-generated filename)?
3. Can the value begin with `-`, or contain a newline, on this path? If the tool honors `--`, is it present?
4. Is the template/expression user-controlled, or is the user only data in a fixed template? Check what is passed as the template argument.
5. Is the code path reachable by an unprivileged actor, or only by CI/maintainer config trusted by the product?
6. Confirm: a test with a benign marker value (`a b; c`, `-x`, `$(id)` as a literal) shows the child process argv/ command line contains it split or interpreted (mock `spawn` and assert argv).

## Severity cues
- Raises: unauthenticated or low-privilege actor, shell reachable, process runs with production credentials, no container isolation.
- Lowers: argv-only with a narrow flag surface, admin-only trigger, value must pass a strict allowlist, sandboxed worker without network or secrets.
- Template injection with a user-editable template is code execution unless the engine is truly sandboxed.

## Regression test
- Fails before: call the handler with a filename `a b; touch x` (or `report $(x).pdf`) and assert the mocked executor receives it as ONE argv element, or that the request is rejected; before the fix argv splits or a shell is invoked.
- Argument injection: pass `-o` or `--help` as the value; assert 400 or that it appears after `--`.
- Template: render with `{{ 7*7 }}` in a user field; assert output contains the literal text, not `49`.
- Allowed case: filename with spaces, unicode, and a legitimate format name still produces the expected invocation.
