---
name: installing-julia
description: Use when your machine does not have JuliaLang runtime
---

# Installing Julia

If your machine does not have the Julia programming language runtime installed, follow the instructions below to install it.

## Preferred: official installer

On macOS or Linux, run the following command:

```sh
$ curl -fsSL https://install.julialang.org | sh -s -- --yes
```

On Windows, run the following command in PowerShell:

```PS
PS> winget install --name Julia --id 9NJNWW8PVKMN -e -s msstore
```

## Fallback: direct tarball install

Use this method when the `curl | sh` installer cannot run — for example, when a
sandbox or permission policy blocks piping a remote script directly into `sh`
(the "Code from External" pattern). This downloads the same official Julia
binary the installer would fetch, but as a plain file you extract locally
— no shell-pipe-to-interpreter.

### Steps (macOS / Linux)

1. Detect platform with `uname -s` (Linux / Darwin) and `uname -m` (x86_64 / aarch64 / arm64).

2. Pick the URL fragment matching your platform:

   | OS / Arch              | URL path        | Tarball suffix         |
   |------------------------|-----------------|------------------------|
   | Linux x86_64           | `linux/x64`     | `linux-x86_64.tar.gz`  |
   | Linux aarch64          | `linux/aarch64` | `linux-aarch64.tar.gz` |
   | macOS x86_64 (Intel)   | `mac/x64`       | `mac-x86_64.tar.gz`    |
   | macOS aarch64 (Apple)  | `mac/aarch64`   | `macaarch64.tar.gz`    |

3. Resolve the latest stable patch (see [[finding-latest-julia-version]] for
   the full set of methods — do not hard-code `VERSION=` from memory), then
   download and extract:

   ```sh
   VERSION=$(curl -fsSL https://julialang-s3.julialang.org/bin/versions.json \
     | jq -r 'to_entries | map(select(.value.stable)) | map(.key)
              | sort_by(split(".") | map(tonumber? // 0)) | last')
   MINOR=${VERSION%.*}             # → e.g. 1.12
   ARCH_PATH=linux/aarch64         # ← from table above
   ARCH_SUFFIX=linux-aarch64       # ← from table above

   mkdir -p ~/julia-install && cd ~/julia-install
   curl -fsSLO "https://julialang-s3.julialang.org/bin/${ARCH_PATH}/${MINOR}/julia-${VERSION}-${ARCH_SUFFIX}.tar.gz"
   tar -xzf "julia-${VERSION}-${ARCH_SUFFIX}.tar.gz"
   export PATH="$HOME/julia-install/julia-${VERSION}/bin:$PATH"
   julia --version
   ```

4. To persist `PATH` across sessions, append the `export PATH=...` line to
   `~/.bashrc`, `~/.zshrc`, or the appropriate shell profile.

### Windows fallback

If `winget` is unavailable, download the `.zip` package from
<https://julialang.org/downloads/>, extract it, and add the inner `bin\` directory to `PATH`.

### Notes

- The tarball is the same artifact the official installer / `juliaup` would fetch — only the delivery mechanism differs.
- Version switching via `juliaup add <version>` is NOT available with this method; install another tarball to use a different version.
- In container or CI environments where `PATH` is set per-command, reference `julia` by full path (`$HOME/julia-install/julia-<VERSION>/bin/julia`) instead of relying on shell profile.
