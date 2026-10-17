---
name: creating-julia-test-env
description: Use when you add tests for Julia packages
---

# creating-julia-test-env

A minimal Julia package layout looks like this:

```sh
$ tree
.
├── Project.toml
└── src
    └── MyPkg.jl # Assume the package is named MyPkg for this example.

```

To add software tests for this package, follow the steps below.

Step 1: Create the `test` directory, `runtests.jl`, and a `Project.toml` for the test environment.

```sh
mkdir test
touch test/runtests.jl
touch test/Project.toml
```

Step 2: Add a `[workspace]` section to `./Project.toml` (not `test/Project.toml`):

```toml
name = "MyPkg"

...
...<omitted>
...

# Add this section
[workspace]
projects = ["test"]
```

---

**Note:** If you are on Julia 1.11 or older, do **not** use `[workspace]`. Instead, add `[extras]` and `[targets]`:

```toml
[extras]
Test = "8dfed614-e22c-5e08-85e1-65c5234f0b40"

[targets]
test = ["Test"]
```

Step 3: Set up `./test/Project.toml` as follows:

```sh
$ cd test
$ ls
runtests.jl Project.toml
$ julia --project -e 'using Pkg; Pkg.add("Test")'
$ julia --project -e 'using Pkg; Pkg.develop(path="../")'
$ cat Project.toml
[deps]
MyPkg = <UUID for MyPkg goes here>
Test = "8dfed614-e22c-5e08-85e1-65c5234f0b40"

[sources]
MyPkg = {path = ".."}
```

Step 4: Put a simple sample test in `test/runtests.jl` (replace `MyPkg` with your actual package name).

```julia
using Test

using MyPkg

@testset "sample" begin
    @test 1 + 1 == 2
end
```

Step 5: Run the following to verify:

```sh
$ julia --project -e 'using Pkg; Pkg.test()'
```
