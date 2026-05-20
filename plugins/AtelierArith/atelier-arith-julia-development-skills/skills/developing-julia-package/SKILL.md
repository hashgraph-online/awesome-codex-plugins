---
name: developing-julia-package
description: Use when you write a Julia package
---

# Developing a Julia package

Notes on developing Julia packages.

Assume the package is named `MyPkg`. Substitute your actual package name wherever `MyPkg` appears.

Use `src/MyPkg.jl` as the package entry point. Keep the module declaration, exports, and `include` list there; put substantial implementation in focused files under `src/`.

```julia
module MyPkg

export fit_model, FitResult, GaussianModel

include("models.jl")
include("fit.jl")
include("preprocess.jl")

end
```

Split files to improve readability, not to recreate Python-style class or submodule hierarchies. Prefer one public module unless there is a real user-facing namespace boundary.

Guidelines below.

## Avoid excessive `export`s

- Do not `export` helpers that are only used internally just so tests can reach them. Prefer importing explicitly in tests:

```julia
# test/runtests.jl

using Test
using MyPkg: <internal-only helper>
```

Test public behavior through the public API first. Import internals only when the helper has meaningful behavior that is hard to exercise through the public path:

```julia
using Test
using MyPkg
using MyPkg: initial_guess

@testset "fit_model" begin
    result = fit_model(x, y; model = GaussianModel())
    @test result isa FitResult
end

@testset "initial_guess" begin
    @test initial_guess(x, y, GaussianModel()) isa NamedTuple
end
```

## Julia-idiomatic style

### Multiple dispatch

Prefer splitting behavior across methods instead of a large `if`/`elseif` chain on `isa`, unlike typical Python style.

```julia
# Do not write if else end
function f(x)
    if x isa Integer
        return 2x
    else
        return x
    end
end
```

Instead, use multiple dispatch:

```julia
f(x) = x # generic implementation
f(x::Integer) = 2x # specialized implementation for x::Integer
```

For package APIs, make the dispatch object explicit and keep symbol options as a thin compatibility layer if needed:

```julia
abstract type AbstractModel end

struct GaussianModel <: AbstractModel
    baseline::Bool
end

GaussianModel(; baseline = true) = GaussianModel(baseline)

fit_model(x, y; model::AbstractModel = GaussianModel()) =
    fit_model(model, x, y)

function fit_model(model::GaussianModel, x, y)
    guess = initial_guess(x, y, model)
    # gaussian-specific implementation
end
```

Use a marker or configuration struct for the model choice, and use a separate result struct for fitted values. Do not mutate a model type into a mixed "algorithm plus fitted state" object unless that is clearly the public contract.

```julia
struct FitResult{P,T}
    params::P
    residuals::Vector{T}
    converged::Bool
end
```

This keeps `GaussianModel()` as the method-selection/configuration value and `FitResult` as the returned fitted state.

### Type annotations

- On **public** APIs, narrow signatures when it prevents misuse or clarifies the contract.
- Inside the package, avoid over-constraining types everywhere; leave room for the compiler and for generic code.

### Type stability

- On hot paths, avoid return types that vary unpredictably across inputs (type instability hurts specialization).
- Confirm bottlenecks with profiling before micro-optimizing.

## Code formatting (JuliaFormatter)

- Format package sources with **[JuliaFormatter.jl](https://github.com/domluna/JuliaFormatter.jl)** so layout and whitespace stay consistent across contributors and CI.
- Optionally commit a **`.JuliaFormatter.toml`** at the repository root (or rely on defaults) so everyone applies the same rules.

From the package root:

```julia
using JuliaFormatter
format(".")  # formats src/, test/, etc. under the current directory
```

Run formatting before merging substantive edits; wire the same command into CI or pre-commit hooks if the team wants enforcement.

## Performance and allocations

- Measure with **`@benchmark` / `@btime`** from BenchmarkTools.jl rather than guessing.
- Watch unnecessary array copies from slicing and broadcasting; when an in-place API is needed, expose it explicitly (separate function name or keyword argument) so callers opt in.

## Errors and documentation

- Raise **`ArgumentError`**, **`DomainError`**, or other appropriate exceptions; messages should tell the caller what to fix.
- Give **docstrings** to exported/public functions—ordinary docstrings above definitions integrate cleanly with Documenter.jl; use `@doc` when you attach documentation programmatically.
