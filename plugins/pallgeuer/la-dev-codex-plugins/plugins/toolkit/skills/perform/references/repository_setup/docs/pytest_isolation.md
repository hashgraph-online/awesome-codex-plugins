# Pytest working-directory isolation

The optional pytest integration gives explicitly opted-in tests a private working directory and can place otherwise unmarked tests in one configured session-shared guard. Explicit tests choose one of two private isolation modes according to what the test should be allowed to do in its current working directory.

## Isolation modes at a glance

The plugin defines two markers, with matching fixtures:

- `@pytest.mark.isolated_cwd` provides a fresh, writable working directory. Use it for code that intentionally reads or writes relative paths, so its files stay inside a disposable per-test sandbox instead of reaching the checkout.
- `@pytest.mark.guarded_cwd` provides a read-only working directory containing deliberately malformed configuration. Use it for code that should not depend on the process working directory, so accidental relative file access, output, or configuration discovery becomes visible during the test.

Use a marker when the test only needs the isolation behavior. Request the matching `isolated_cwd` or `guarded_cwd` fixture when the test also needs the working-directory path. Markers can also be applied at class or module scope to establish the mode for a group of tests.

Installing the package never activates the plugin automatically: there is no `pytest11` entry point. Loading the plugin also leaves unmarked tests untouched by default, without working-directory mutation, environment mutation, or temporary-directory allocation. A downstream suite may separately configure the shared guard described below. The two explicit private modes are alternatives and cannot be combined on one test.

## Installation and loading

Install the narrow extra or the equivalent development extra:

```text
python -m pip install 'la-dev-codex-plugins[pytest]'
python -m pip install 'la-dev-codex-plugins[dev]'
```

Both extras declare `pytest>=7.0.1`; the base installation remains dependency-free. Explicitly load the plugin on the command line:

```text
pytest -p la_dev_codex_plugins.pytest_isolation.plugin
```

Alternatively, opt in for a repository or test subtree from its pytest configuration:

```python
pytest_plugins = ("la_dev_codex_plugins.pytest_isolation.plugin",)
```

The `la_dev_codex_plugins.pytest_isolation` package itself does not import pytest or eagerly load the plugin. Register the plugin during pytest's normal initial plugin configuration; dynamic registration after `pytest_sessionstart` is unsupported. Downstream suites must not override the `guarded_cwd` or `isolated_cwd` fixture names while using the plugin; fixture overriding would make request-based activation ambiguous and is unsupported. Shared policy customization uses the process-global pytest hook documented below.

## Git environment isolation

Active private or shared working-directory isolation clears inherited Git repository-local environment variables by default. Git hooks can export an absolute `GIT_INDEX_FILE`, particularly during `git commit -a`; changing directories alone then leaves temporary test repositories using the caller's index. Clearing the inherited state lets each temporary repository use its own index, object store, and configuration.

`la_dev_cwd_isolation_git_environment` is a process-wide string-valued ini option with exactly two accepted values:

- `clear`, the default, saves the exact presence and values of managed Git variables, clears them when isolation activates, and restores the saved state when the boundary ends.
- `inherit` leaves Git environment variables unmanaged, including any changes tests make. Use this compatibility setting when tests intentionally inherit repository routing, shared object stores, or command configuration:

```toml
[tool.pytest.ini_options]
la_dev_cwd_isolation_git_environment = "inherit"
```

There is no additional command-line option, environment alias, marker argument, or per-test override. Invalid values, including empty, differently cased, and whitespace-polluted values, are usage errors before isolation allocation. Loading the plugin with no active private or shared isolation remains inert with either setting.

The maintained list matches Git's repository-local environment names reported by `git rev-parse --local-env-vars`:

```text
GIT_ALTERNATE_OBJECT_DIRECTORIES
GIT_COMMON_DIR
GIT_CONFIG
GIT_CONFIG_COUNT
GIT_CONFIG_PARAMETERS
GIT_DIR
GIT_GRAFT_FILE
GIT_IMPLICIT_WORK_TREE
GIT_INDEX_FILE
GIT_NO_REPLACE_OBJECTS
GIT_OBJECT_DIRECTORY
GIT_PREFIX
GIT_REPLACE_REF_BASE
GIT_SHALLOW_FILE
GIT_WORK_TREE
```

Other variables remain unchanged, including Git identity, tracing, and global/system configuration controls. Indexed `GIT_CONFIG_KEY_n` and `GIT_CONFIG_VALUE_n` entries remain unchanged; clearing `GIT_CONFIG_COUNT` disables their inherited use. Tests explicitly setting a new count should also supply their own corresponding keys and values.

Private isolation clears the variables before downstream function fixtures run and keeps test-defined values available through their finalizers. Broader fixtures retain the original environment unless shared guarding is enabled. Shared mode clears the variables from collection finish through session teardown and reasserts that state at the same activation points as temporary-directory redirection: before each test, before private allocation, after private teardown, and after broader fixture finalization. Nested private teardown restores the cleared shared environment; final shared teardown restores the caller's exact environment. Normal failures, skips, partial setup failures, and interrupt unwinding use the same restoration lifecycle.

Tests may explicitly configure Git variables after isolation begins. Clearing inherited command configuration also removes inherited `git -c` settings, and clearing object-store variables can affect projects intentionally reusing external objects; select `inherit` when that inheritance is required. The plugin uses a fixed-size list and never launches Git for discovery, so Git remains optional and activation overhead consists only of environment operations.

## Cleanup lifecycle

`la_dev_cwd_isolation_cleanup` is a process-wide string-valued ini option with exactly two accepted values:

- `eager`, the default, restores process state and immediately removes each safely verified isolation boundary through descriptor-anchored cleanup.
- `pytest_retained` restores process state and verifies each boundary, then leaves safely verified boundaries below pytest's base temporary directory for a later pytest invocation to prune.

There is no command-line alias, environment-variable alias, marker argument, fixture argument, or policy-hook key for cleanup mode. Empty, unknown, differently cased, and whitespace-polluted values are usage errors before test execution and isolation allocation. Loading the plugin with the default and without shared guarding or an explicitly isolated test remains inert and does not initialize pytest's base temp or mutate process state.

Retained mode is useful when a cooperative long-lived resource stores interpreter-owned state in the redirected temporary directory and completes its lifecycle only during interpreter shutdown. The plugin does not inspect or specialize for any such resource. Configure it with pytest's successful-session retention enabled:

```toml
[tool.pytest.ini_options]
la_dev_cwd_isolation_cleanup = "pytest_retained"
tmp_path_retention_policy = "all"
tmp_path_retention_count = 3
```

Without `--basetemp`, pytest versions exposing `tmp_path_retention_policy` and `tmp_path_retention_count` require policy `all` and a count of at least one. Policies `failed` and `none`, or a zero count, can delete the current base temp before interpreter shutdown and are rejected. Pytest 7.0.1 has fixed three-session retention and is accepted without those newer settings. Supplying `--basetemp` is also accepted regardless of numbered-directory retention settings; pytest clears that explicit directory at the start of a later invocation instead of applying successful-session numbered-directory pruning. Retained mode never silently falls back to eager cleanup.

In retained mode, the shared boundary is a direct child of the current process's pytest base temp. Explicit private boundaries remain below the shared `tmp/` when shared guarding is active, preserving neutral boundary-file ancestry. Without shared guarding, private boundaries are direct children of the pytest base temp. Pytest-managed `tmp_path` and `tmpdir` artifacts remain ordinary siblings rather than becoming children of an isolation boundary. Each xdist worker initializes and uses its own factory and base-temp allocation without shared coordination.

Both modes restore the exact saved CWD, managed environment-variable presence and values, and `tempfile.tempdir`, then verify recorded boundary identities and any shared policy manifest. Eager mode additionally restores permissions and removes the verified tree immediately. Retained mode stops after successful verification without traversing arbitrary writable `tmp/` contents. Missing or identity-replaced entries and otherwise identity-uncertain state are reported and preserved in either mode. Mode or policy corruption is reported; eager mode may still remove the tree when every recorded identity remains safely verified, while retained mode preserves it. A safely retained nested private boundary is complete and does not block the outer shared lifecycle.

Retained boundaries and standard temporary artifacts therefore consume disk for pytest's configured retention window and remain available for debugging. A later pytest invocation may prune the entire old base temp using pytest's cleanup implementation, not the plugin's descriptor-anchored identity checks. Suites selecting this cooperative lifecycle must not place valuable or externally moved data in isolation boundaries or deliberately replace recorded paths. Retained cleanup provides lifecycle compatibility and correctness isolation, not a stronger security sandbox.

## Shared guard for unmarked tests

A suite can opt every otherwise unmarked test into one shared guarded CWD with this exact `pyproject.toml` configuration:

```toml
[tool.pytest.ini_options]
la_dev_cwd_isolation_unmarked = "shared_guarded"
```

`la_dev_cwd_isolation_unmarked` is string-valued. Its accepted values are `none`, the default described above, and `shared_guarded`. Every other value, including differently cased or whitespace-polluted spellings, is a usage error before test execution or shared filesystem allocation. There are no command-line aliases or environment-variable equivalents.

With `shared_guarded`, each pytest process creates one session boundary using the usual `cwd/` and `tmp/` layout. Each xdist worker is a separate process and therefore creates its own boundary; no xdist integration or cross-worker state is involved. Session start resolves the policy and initializes pytest's temporary factory, then the end of collection creates and hardens the shared guard before the first test even when that test requests private isolation. The process remains in its ordinary CWD between tests.

Before pytest sets up any fixture for an item, the plugin verifies the recorded identities and modes of the shared boundary, guarded `cwd/`, and writable `tmp/`, then enters the verified CWD descriptor. Unmarked tests and all broader-scoped fixtures remain in that stable shared layer. An explicitly private test temporarily enters its unique private boundary for function-scoped fixtures and the test body, restores the shared layer before module- or session-scoped fixture finalizers run, and finally leaves the shared layer after pytest completes the item's broader fixture teardown. Without configured shared mode, broader fixtures instead use the ordinary process CWD. An escaped, inaccessible, deleted, symlink-substituted, identity-replaced, or root-mode-mutated shared layout fails concisely after restoration is attempted. Layout corruption also fails before another test or nested private allocation can use the guard, and the plugin never reconstructs a deliberately corrupted shared tree.

The default shared poison policy contains the same malformed `pyproject.toml` used by private guarded mode. A project can replace it and optionally create a neutral configuration boundary above both `cwd/` and `tmp/` by implementing one process-global hook in the root `conftest.py` or an early-loaded pytest plugin:

```python
def pytest_la_dev_cwd_isolation_shared_policy(config):
    return {
        "boundary_files": {
            "pyproject.toml": "[tool.project]\n",
        },
        "poison_files": {
            "pyproject.toml": "[tool.project_specific_guard\n",
            "config/tool.ini": "[invalid",
        },
    }
```

The hook may return `None` or a mapping containing only `boundary_files` and `poison_files`. There may be at most one non-`None` provider in a pytest process. A conftest below pytest's root is rejected because partial path selection may not load it; this includes provider objects whose hook implementation is defined by a registered nested conftest. Placing the provider at the root or in an early plugin makes the policy independent of collection order and selected test paths. Early plugin modules are identified by how pytest loaded them rather than by filename, so a deliberately loaded plugin module named `conftest.py` remains valid. Under the cooperative-suite contract, opaque provider objects that cannot be attributed to a conftest are treated as early-plugin registrations. Omitting `poison_files` retains the default, while specifying it uses complete replacement semantics and `{}` creates a poison-free read-only guard. Omitting `boundary_files` creates no neutral ancestor files. The boundary mapping cannot use the reserved `cwd/` or `tmp/` paths.

Both values must map filesystem-encodable string relative paths to UTF-8-encodable string contents and follow the private poison policy's normalization and collision rules. Files receive mode `0400` and nested policy directories receive mode `0500`. The plugin copies and validates the complete policy once at session start, before initializing pytest's temporary root or creating its own boundary, so later source-mapping mutation cannot change the active policy. Boundary creation records an exact compact manifest of expected paths, entry types, modes, and SHA-256 content hashes, then releases the original path-to-content mappings. Session teardown validates the boundary and guarded policy trees against this manifest before cleanup; only the writable `tmp/` subtree may contain arbitrary entries. This one-time exact check detects policy corruption without multiplying policy-tree traversal by the number of tests. Invalid global policy produces one pytest usage error rather than one fixture error per test.

From collection finish through session finish, `TMPDIR`, `TEMP`, and `TMP` point to the shared writable `tmp/`, and `tempfile.tempdir` is cleared so standard-library temporary APIs rediscover it. The lifecycle layers verify the fixed-size shared layout and reassert those values before every test, before private allocation, after private function-fixture teardown, and after broader fixture finalization, preventing direct process-global mutations from leaking to later tests. The directory persists across tests, although standard temporary APIs continue to create unique descendants. An explicitly private test temporarily redirects these values to its own private `tmp/`, then restores and revalidates the canonical shared values.

Pytest's own `tmp_path` and `tmpdir` factory is initialized before collection and session redirection, so pytest-managed artifacts remain outside the plugin boundary and follow pytest's normal retention and permission behavior. The plugin preserves `tempfile.tempdir` around that initialization, preventing pytest's call to `tempfile.gettempdir()` from populating the process cache before collection. The plugin does not chmod pytest-owned paths. Standard-library temporary artifacts remain inside shared `tmp/`; eager mode removes them with the plugin boundary, while retained mode leaves them for later pytest pruning. At session teardown, the plugin restores the exact initial CWD, environment-variable presence and values, and prior `tempfile.tempdir`, then opens the recorded boundary, `cwd/`, and `tmp/` through verified no-follow descriptors before finalizing the lifecycle. Missing or identity-replaced children preserve the complete boundary without traversal. If cleanup of a nested private boundary was incomplete, the plugin verifies the accessible shared layout and policy but preserves the complete shared boundary instead of allowing outer eager cleanup to traverse the uncertain private root. Mode or policy corruption is reported; eager mode may still remove the tree when every recorded identity remains safely verified, while retained mode preserves it.

Explicit isolation takes precedence for function-scoped fixtures and the test body. `isolated_cwd` creates its usual private writable boundary, and `guarded_cwd` creates its usual private guarded boundary with marker-specific poison merge or replacement semantics. Session- and module-scoped fixtures remain in the stable outer shared guard, while these per-test boundaries are intentionally nested below shared `tmp/`, so boundary policy files form a neutral ancestor for private working directories as well. Here, private means unique to one test, not independent of the shared filesystem root. A matching marker and fixture still create one private boundary. Explicit opposite modes remain an error. The `guarded_cwd` fixture never returns the shared path, and no fixture exposes that path; a shared test can inspect `pathlib.Path.cwd()` when needed.

Shared guarding is correctness isolation for cooperative test suites, not a security sandbox against code already running with the pytest process's privileges. Tests must not deliberately chmod, replace, delete, add to, race, or mutate the shared guarded or boundary policy trees; use explicit `isolated_cwd` or private `guarded_cwd` for intentional CWD manipulation. Recorded layout identity and root-mode changes fail immediately, while nested policy modes, contents, and unexpected entries are reported by the exact session-teardown check and may therefore affect intervening tests. Descriptor-anchored cleanup still refuses to traverse an identity-uncertain recorded boundary, `cwd/`, or `tmp/`, and an uncertain nested private boundary prevents deletion of its outer shared boundary. Owner mode bits remain advisory for root/elevated users and filesystems that do not enforce them. CWD, environment variables, `tempfile.tempdir`, and umask are process-global and must not race in-process threads. Native Windows and WSL remain unsupported.

## Writable isolation: `isolated_cwd`

Request the fixture when the test needs the directory path:

```python
def test_generates_files(isolated_cwd):
    output = isolated_cwd / "output.txt"
    output.write_text("result", encoding="utf-8")
```

Use the marker when the path is not needed as an argument:

```python
import pytest


@pytest.mark.isolated_cwd
def test_uses_relative_paths():
    ...
```

The test begins in a fresh writable `cwd/`. It may finish in another accessible directory; the plugin silently restores the original CWD because legitimate sandboxed code can call `chdir`. It fails the affected test only if the final CWD cannot be inspected or the original CWD cannot be restored.

## Guarded isolation: `guarded_cwd`

Guarded mode exposes accidental reads from or writes to the current working directory:

```python
import pytest


@pytest.mark.guarded_cwd
def test_does_not_discover_cwd_configuration():
    ...
```

The fixture form returns the guarded path:

```python
def test_stays_inside_guard(guarded_cwd):
    assert guarded_cwd.name == "cwd"
```

By default, `cwd/pyproject.toml` contains the exact UTF-8 text `[tool.la_dev_cwd_guard\n`, which is deliberately malformed. Before test code runs, every directory in the guarded tree has mode `0500` and every poison file has mode `0400`.

Customize poison files on the nearest applicable marker:

```python
@pytest.mark.guarded_cwd(
    poison_files={"config/tool.ini": "[invalid"},
    include_default_poison=False,
)
def test_custom_guard():
    ...
```

`poison_files` must be `None` or map filesystem-encodable string relative paths to UTF-8-encodable string contents. `None` is equivalent to an empty custom mapping, so the default poison remains controlled by `include_default_poison`. Contents are written exactly as UTF-8 without an implicit newline. Supplied entries override the default at the same normalized path. Absolute, empty, `.`, and any path containing a `..` component are rejected, as are duplicate normalized paths and file/directory collisions. `include_default_poison` must be a Boolean and defaults to `True`. No positional or unknown marker arguments are accepted.

A guarded test must finish in its guarded `cwd/`. Directory identity rather than lexical spelling is compared, so equivalent paths through a symlinked temporary root are accepted. Finishing in another accessible directory is a leak and fails the test after restoration. An inaccessible or deleted final CWD, or a failure to inspect its identity, also fails after restoration. Finalization verifies the boundary and original guarded identity. Eager cleanup then restores directory traversal permissions and removes the tree in one no-follow descriptor traversal; retained cleanup leaves the verified tree untouched. Regular files, symbolic links, and special files are never chmodded during eager teardown.

Owner mode bits do not reliably prevent writes by root/elevated users or on filesystems that do not enforce them. The malformed configuration and CWD-leak checks still apply in those environments; tests must not claim that mode bits constrain root.

## Private isolation: Marker inheritance and conflicts

The nearest marker of one name supplies configuration, so a class or function marker can replace a module-level guarded configuration. Repeating the same mode is valid. A matching marker and fixture also activate only one setup/teardown cycle.

Every applicable combination of explicit `guarded_cwd` and `isolated_cwd` is a setup error for the affected test. This includes inherited opposite markers, opposite marker/fixture combinations, and requesting both fixtures. Neither explicit mode silently overrides the other. The configured shared default does not participate in this conflict: either explicit mode overrides it. `isolated_cwd` accepts no arguments.

## Private isolation: Process state and teardown

Every opted-in test receives one private boundary:

```text
la-dev-pytest-isolation-.../
|-- cwd/
`-- tmp/
```

The sibling `tmp/` remains writable in both modes. Before other function-scoped fixtures run, the plugin:

- saves the exact `os.getcwd()` value;
- saves the exact value or absence of `TMPDIR`, `TEMP`, and `TMP`;
- saves and clears the managed Git repository-local variables when the Git environment policy is `clear`;
- saves the exact `tempfile.tempdir` cache;
- points all three environment variables at the absolute `tmp/` path;
- sets `tempfile.tempdir = None` so the standard library rediscovers the redirected directory; and
- changes to `cwd/`.

The private boundary and writable directories receive explicit owner-accessible modes after creation, so a restrictive process umask cannot make isolation setup or cleanup unusable. Guarded mode subsequently applies its documented read-only owner modes to the guarded tree while leaving `tmp/` writable.

A plugin-wide function-scoped autouse dispatcher enters private isolation after broader fixture setup but before downstream function-scoped fixtures, and leaves it after those function fixtures finalize but before module- or session-scoped finalizers. The private teardown inspects the test's final CWD, attempts to restore the outer CWD, restores all managed environment variables and the exact `tempfile.tempdir` value, and finalizes the boundary through verified descriptors according to the configured cleanup mode. An outer runtest-protocol hook performs emergency restoration when Ctrl-C or `pytest.exit()` bypasses normal teardown; setup and emergency restoration preserve the original exception or interrupt even when restoration also reports failures. Restoration is attempted before ordinary leak failures are reported, including after assertion failures, skips, fixture failures, and partial isolation setup failures. Boundary construction records each identity before subsequent fallible setup work. If restoring the original CWD fails, environment restoration and boundary finalization still proceed. Finalization opens and verifies the recorded boundary, `cwd/`, and `tmp/`; any missing or changed recorded identity preserves the boundary and replacement rather than deleting uncertain data. Under eager cleanup, writable descendants have owner access restored descriptor-relatively before they are opened, allowing permission-testing trees to be cleaned without following symbolic links. Policy verification and eager cleanup use iterative descriptor stacks rather than Python recursion; descriptor exhaustion is reported as an ordinary teardown failure and preserves the affected boundary.

CWD and environment variables are process-global. Privately isolated tests must not race threads that use either state. Each pytest-xdist worker is a separate process and receives independent private per-test boundaries; the plugin does not provide thread isolation.

The integration officially supports Ubuntu 18.04 or newer and macOS 14 or newer. General POSIX Linux compatibility is intended. Native Windows and WSL are unsupported and untested.

Private isolation without configured shared mode deliberately does not invent a neutral pytest configuration boundary. Eager standalone private boundaries use the ambient standard temporary location, while retained standalone private boundaries use pytest's base temp. In shared mode, downstream projects can use `boundary_files` to stop tool-specific ancestor configuration discovery for both shared and nested private working directories.
