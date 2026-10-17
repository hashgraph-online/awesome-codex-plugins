---
name: using-bgs-papyrus
description: Use when the user wants to compile Papyrus PSC to PEX, decompile PEX to PSC, detect Creation Kit Papyrus toolchains, or inspect Papyrus capabilities for Skyrim, Fallout 4, or Starfield. Triggers - "compile PSC", "decompile PEX", "PapyrusCompiler", "bgs-papyrus", "Starfield Guard syntax".
---

# Using bgs-papyrus

`bgs-papyrus` is the agent-native CLI for Papyrus compile and decompile work. It detects official Creation Kit compilers, compiles `.psc` to `.pex`, decompiles `.pex` to `.psc` through Champollion, and returns JSON envelopes for agent workflows.

Use this skill for:

- compiling Papyrus source to bytecode for Skyrim LE, Skyrim SE/AE, Fallout 4, or Starfield;
- decompiling Papyrus bytecode to source for inspection or patching;
- detecting whether the official Creation Kit compiler and Champollion are available;
- handling Starfield Guard syntax produced by Champollion.

Do not use this skill for plugin record edits, load-order edits, or BA2/BSA packing. Route those through the xEdit, load-order, or archive skills.

## Prerequisites — detect first

Always query the live CLI before choosing a backend or game path:

```powershell
bgs-papyrus capabilities --json
bgs-papyrus detect-toolchain --json --game starfield
```

The official Creation Kit must be installed by the user from Steam. Bethesda's `PapyrusCompiler.exe` is not bundled with this plugin and must not be copied into the repo or plugin tree. `bgs-papyrus` detects and drives the installed compiler.

Champollion is used for decompile. `bgs-papyrus` detects Champollion; it does not download it automatically. Install `Champollion.exe` at:

```text
~/.bgs-modding-superpowers/tools/champollion/Champollion.exe
```

or the user can set `BGS_PAPYRUS_CHAMPOLLION` to an existing executable.

One PowerShell install shape for Champollion v1.3.2 from `Orvid/Champollion` releases:

```powershell
$root = "$HOME\.bgs-modding-superpowers\tools\champollion"; New-Item -ItemType Directory -Force -Path $root | Out-Null; $zip = Join-Path $root "Champollion.v1.3.2.zip"; Invoke-WebRequest "https://github.com/Orvid/Champollion/releases/download/v1.3.2/Champollion.v1.3.2.zip" -OutFile $zip; Expand-Archive -Force $zip $root
```

Human manuals:

- English: `tools/bgs-papyrus/USER-GUIDE.en.md`
- Chinese: `tools/bgs-papyrus/USER-GUIDE.zh-cn.md`

## Hard rules

- Never write compiled `.pex` output into the game's `Data` folder or any Stock-Game tree.
- Game-ready compiled output belongs in an MO2 mod overlay: `<MO2_Root>/mods/<mod-name>/Scripts/`.
- Use `--json` for agent workflows and branch on the envelope, not human text.
- Detect the toolchain before compile/decompile. Do not guess that a compiler path exists.
- Starfield compile should use the official CK compiler for Guard syntax. Caprica and russo are non-Guard fallbacks.

## Commands

Check `bgs-papyrus --help` and `<subcommand> --help` for the current option surface. The examples below are templates.

### `capabilities`

Discover supported games, subcommands, backends, flags files, and Starfield syntax behavior.

```powershell
bgs-papyrus capabilities --json
```

### `detect-toolchain [--game G]`

Find installed official CK compilers and the Champollion decompiler.

```powershell
bgs-papyrus detect-toolchain --json --game fallout4
bgs-papyrus detect-toolchain --json
```

Supported game arguments are `skyrimle`, `skyrimse`, `fallout4`, and `starfield`. Fallout 3, Fallout: New Vegas, and Oblivion do not use Papyrus and are out of scope.

### `compile <src> --game G`

Compile one `.psc` file, or use `--all` for a directory.

```powershell
bgs-papyrus compile "D:\work\Scripts\Source\MyQuestScript.psc" --json --game starfield --out "D:\work\compiled" --import "D:\work\Scripts\Source"
```

Useful options:

- `--out <dir>`: output directory.
- `--import <dir>`: source import directory; repeat for multiple roots.
- `--backend ck|caprica|russo|auto`: compiler backend.
- `--flags <file>`: explicit flags file.
- `--optimize`, `--release`, `--final`, `--all`: compile options.

For final game use, copy the resulting `.pex` into an MO2 overlay:

```text
<MO2_Root>/mods/<mod-name>/Scripts/
```

Never write the result to `<game>/Data/Scripts/` directly.

### `decompile <src> --game G`

Decompile one `.pex` file, or use `--recursive` for a directory.

```powershell
bgs-papyrus decompile "D:\mods\Example\Scripts\MyQuestScript.pex" --json --game starfield --out "D:\work\decompiled"
```

Useful options:

- `--out <dir>`: output directory.
- `--recursive`: decompile a directory tree.
- `--threaded`: use Champollion threaded mode where supported.
- `--sf-syntax-fix` / `--no-sf-syntax-fix`: enable or disable Starfield syntax post-processing.

## Starfield specifics

The official Starfield CK compiler handles Guard syntax natively. Champollion v1.3.2 guesses some Guard syntax in a form that the CK does not accept, so `bgs-papyrus` applies a validated Starfield syntax post-process during decompile:

```text
Guard ... EndGuard       -> LockGuard ... EndLockGuard
TryGuard ... EndGuard    -> TryLockGuard ... EndTryLockGuard
```

This Guard rewrite was checked by recompiling the decompiled output through the real Starfield CK compiler.

Known limitation: Champollion v1.3.2 has unrelated decompile bugs, such as remote-event casts, that can stop complex vanilla scripts from recompiling cleanly. Treat decompiled output as a strong starting point and manually fix compiler-rejected constructs. The Guard post-processor is validated; this limitation is upstream Champollion.

## Safe workflow pattern

1. Run `bgs-papyrus capabilities --json`.
2. Run `bgs-papyrus detect-toolchain --json --game <game>`.
3. Compile or decompile with `--json`.
4. For compile output, stage final `.pex` files only under `<MO2_Root>/mods/<mod-name>/Scripts/`.
5. For decompile output intended for reuse, recompile it through the official CK compiler before claiming it is publishable.
