---
name: running-julia-test
description: Use when you run tests
---

# Running Julia tests

## Running all tests with `Pkg.test()`

Before running tests for a new package, make sure the test environment is already set up. If the package does not have tests yet, follow `creating-julia-test-env` first. Tests that use `using Test` must have `Test` available from the package or test project.

To run all of your package's tests, use the following command:

```sh
$ julia --project -e 'using Pkg; Pkg.test()'
```

## Running specific test sets only

To run only particular test sets (for example, those defined as `@testset "label" begin ... end`), use the `~/.julia/bin/testrunner` tool.

If `testrunner` is already installed, this command prints its path:

```sh
$ command -v testrunner
```

If you do not have the `testrunner` command, install it with:

```sh
$ julia -e 'using Pkg; Pkg.activate(); Pkg.Apps.add(url="https://github.com/aviatesk/TestRunner.jl")'
```

### Basic Usage

```bash
$ testrunner demo.jl "basic tests"                   # Run the testset named "basic tests"

$ testrunner demo.jl "basic tests" "struct tests"    # Run multiple named testsets

$ testrunner demo.jl '(:(@test startswith(inner_func2(), "inner")))'  # Run a standalone test case
```

See the [guide](https://raw.githubusercontent.com/aviatesk/TestRunner.jl/refs/heads/master/README.md) to learn more.

### Caveat: There are cases where name or regex filters do not work as expected

Sometimes, even after specifying a testset name or a regex, all tests may run instead of just the intended ones (this seems to be due to a pattern matching behavior in TestRunner.jl). Example:

```sh
# Expected: Only "calculate: basic operations" should run (4 tests), but actually all 20 tests run
$ testrunner --project=. test/runtests.jl "calculate: basic operations"
$ testrunner --project=. test/runtests.jl 'r"^calculate: basic operations$"'
$ testrunner --project=. test/runtests.jl L6:11   # Even if you include the @testset declaration line, all tests are executed
```

As a workaround, specify the line range including only the `@test` lines (do not include the `@testset ... begin` declaration line). This way, you can ensure that only the intended testset is executed:

```sh
# In the case where the target @test lines are in lines 7-10 of runtests.jl
$ testrunner --project=. test/runtests.jl L7:10
```

Always confirm whether your filter worked as intended by checking the Total count in the `Test Summary` or the `n_passed` field in the `--json` output.

## Keeping sessions warm with WarmTestRunner.jl

WarmTestRunner.jl is a test runner that accelerates local test iterations while developing Julia packages.

Whereas standard `Pkg.test()` runs your tests in a fresh Julia process every time, WarmTestRunner.jl reuses a daemon process and a pool of warm workers, spreading the loading and compilation cost across multiple test runs.

As a general guideline, use it as follows:

- For everyday edit/test cycles: `using WarmTestRunner; runtests()`
- For final checks before merges, releases, or CI-style runs: `Pkg.test()`

To install WarmTestRunner.jl:

```sh
$ julia -e 'using Pkg; Pkg.activate(); Pkg.develop(url="https://github.com/terasakisatoshi/WarmTestRunner.jl")'
```

### Basic Usage

```sh
$ cd path/to/target/package
$ julia --project -e 'using WarmTestRunner; runtests()'
```

To run testsets in parallel, start the WarmTestRunner daemon with multiple jobs in one terminal, then run tests with `split_testsets = true` from another terminal:

```sh
# Terminal 1
$ cd path/to/target/package
$ julia --project -e 'using WarmTestRunner; serve(jobs=4)'

# Terminal 2
$ cd path/to/target/package
$ julia --project -e 'using WarmTestRunner; runtests(split_testsets = true)'
```

This splits testsets and executes them across the warm worker pool.

When `runtests()` starts the daemon automatically, a daemon process runs in the background. To manually stop any WarmTestRunner daemon, run the following:

```sh
$ cd path/to/target/package
$ julia --project -e 'using WarmTestRunner; stop()'
```

If you run `Pkg.build()` for the target package, stop the daemon (`stop()`) first and rerun `runtests()` afterwards.

This is especially important when developing a Julia package with a C interface. In that workflow, `Pkg.build()` is often used to rebuild or replace a shared library, and WarmTestRunner workers may still have the old shared library loaded. Stop the daemon before rebuilding so the next test run starts from fresh workers:

```sh
$ cd path/to/target/package
$ julia --project -e 'using WarmTestRunner; stop()'
$ julia --project -e 'using Pkg; Pkg.build()'
$ julia --project -e 'using WarmTestRunner; runtests()'
# update files in ./src or ./test/
$ julia --project -e 'using WarmTestRunner; runtests()'
# update files in ./src or ./test/ ... repeat the cycle
```

### Caveat: When the workspace structure changes, run `stop()` first

The daemon caches the path and contents of `Project.toml` into its worker pool at startup, so `runtests()` may fail to start with an error after any of the following **workspace structure changes**:

- Deleting or regenerating `Project.toml` / `Manifest.toml`
- Moving or renaming the package directory
- Editing the `[workspace]` / `[deps]` / `[sources]` sections
- Removing files the worker is still referencing from outside the daemon

Example errors (recorded in the controller log `~/.julia/warmtestrunner/logs/controller-*.err.log`):

```
nested task error: ".../path/to/Project.toml": No such file
ERROR: timed out waiting for server record for ...
```

The recovery procedure is the same as for `Pkg.build()`: **first `stop()`, then run `runtests()` again**:

```sh
$ julia --project -e 'using WarmTestRunner; stop()'
$ julia --project -e 'using WarmTestRunner; runtests()'
```
