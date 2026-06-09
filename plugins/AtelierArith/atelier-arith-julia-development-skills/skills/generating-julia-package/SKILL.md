---
name: generating-julia-package
description: Use when you create a JuliaLang package
---

# Creating a Julia Package

## Project Environment

If you want to create a simple script that depends on external libraries, you should create a "project environment". This means making a `Project.toml` file like the one below.

```toml
[deps]
"<Installed Package 1>" = "<UUID for Installed Package 1>"
"<Installed Package 2>" = "<UUID for Installed Package 2>"
"<Installed Package 3>" = "<UUID for Installed Package 3>"
```

To install an external library (for example, `TargetPackage`), run the following in your terminal:

```sh
julia --project -e 'using Pkg; Pkg.add("TargetPackage")'
```

## Package Directory

If you want to create a reusable package or a larger scale script, you should create a "package directory".

### Choosing the layout

**Default: in-place layout.** Create `./Project.toml` and `./src/MyPkg.jl` directly in the current working directory, with no subdirectory named after the package. Use this whenever the user asks to "create a package `MyPkg`" without further qualification.

**Opt-in: subdirectory layout.** Only use this when the user explicitly asks for a subdirectory — for example "create the package under a new directory", "サブディレクトリを作って", "`MyPkg/` 配下に作って", or when the user is bootstrapping multiple packages side by side under a single workspace and a subdirectory is necessary to disambiguate them.

Do NOT use `Pkg.generate("MyPkg")` for the in-place layout — it always creates a subdirectory. The in-place layout is the default and must be produced by hand-writing the files (see the steps below).

### In-place layout (default, no subdirectory)

To create `Project.toml` and `src/MyPkg.jl` directly in the current working directory:

1. Generate a UUID for the `uuid` field of `Project.toml`:

   ```sh
   $ julia -E 'using UUIDs; string(uuid4())'
   "43d6671a-6eab-408d-9ef9-8f584d9146fb" # Example output.
   ```

2. Write `./Project.toml` with the package name and the UUID from step 1:

   ```toml
   name = "MyPkg"
   uuid = "43d6671a-6eab-408d-9ef9-8f584d9146fb"
   authors = ["Your Name <you@example.com>"]
   version = "0.1.0"
   ```

3. Write `./src/MyPkg.jl` with the module skeleton:

   ```julia
   module MyPkg

   greet() = "Hello"

   end # module MyPkg
   ```

4. Verify by loading the package from the current directory:

   ```sh
   $ julia --project=. -e 'using MyPkg; println(MyPkg.greet())'
   ```

### Subdirectory layout (opt-in only)

Only use this when the user explicitly asks for it. To create a package named `MyPkg` under a new subdirectory, run:

```sh
$ julia -e 'using Pkg; Pkg.generate("MyPkg")'
```

This will create:

```sh
$ tree
.
└── MyPkg
    ├── Project.toml
    └── src
        └── MyPkg.jl

3 directories, 2 files
```
