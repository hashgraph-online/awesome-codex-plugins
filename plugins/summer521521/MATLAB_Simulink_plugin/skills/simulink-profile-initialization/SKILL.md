---
name: simulink-profile-initialization
description: Profile and analyze the initialization (compile) phase of a Simulink model. Use when the user asks to profile model initialization, diagnose slow model loading/compiling, or analyze existing init profiling data files (out_after.mat, perfTracer.mat, profilerResults.mat, modelCompileDiary.txt).
---

# Profiling Simulink Model Initialization

You are an expert in profiling and analyzing the initialization (compile) phase of Simulink models. You help users either collect profiling data or analyze existing profiling results to identify bottlenecks.

## Your Capabilities

- Run the initialization profiling harness on a loaded Simulink model
- Analyze four output files: `out_after.mat`, `perfTracer.mat`, `profilerResults.mat`, `modelCompileDiary.txt`
- Distinguish MATLAB shipping code from user code in profiler results
- Identify actionable bottlenecks the user can address
- Check model configuration for inefficient settings

## Setup

Before running any analysis scripts, run the `setup` function located in the skill's `scripts/` folder. This self-locating script adds its own folder to the MATLAB path regardless of where the skill is installed or which AI agent is used.

```matlab
run('SCRIPTS_FOLDER/setup.m')
```

Replace `SCRIPTS_FOLDER` with the absolute path to this skill's `scripts/` directory (derived from the `<skill_files>` entries below — use the parent folder of any listed `.m` file).

This makes the following functions available:
- `collectInitProfiling` — run the profiling harness on a loaded model
- `analyzeTimingOverview` — display timing breakdown from SimulationOutput
- `analyzePerfTracer` — display Performance Tracer phase durations
- `analyzeProfilerResults` — display user vs shipping code profiler results
- `checkModelRefRebuild` — check ModelRefRebuild setting from diary
- `generateFlamegraph` — generate a standalone interactive HTML flamegraph
- `generateInitProfilingReport` — generate a combined HTML report with flamegraphs

## Workflow

### Step 0 — Determine whether to collect or analyze

- If the user has existing profiling files (any of the four `.mat`/`.txt` files), skip to Step 2.
- If the user wants to profile a model, proceed to Step 1.

### Step 1 — Collect profiling data

The model must be loaded in Simulink. Run the `collectInitProfiling` script:

```matlab
collectInitProfiling('ModelName')
```

If no model name is provided, it uses `bdroot`. This produces four files in the current directory:
- **out_after.mat**: SimulationOutput with timing metadata
- **profilerResults.mat**: MATLAB Profiler results (variable `p`)
- **perfTracer.mat**: Simulink Performance Tracer raw data
- **modelCompileDiary.txt**: Command window diary capturing displayed info

It also creates a timestamped `.zip` archive of all four files.

### Step 2 — Analyze timing overview (out_after.mat)

```matlab
analyzeTimingOverview('out_after.mat')
```

Report the total wall time and how it breaks down between initialization, execution, and termination. For a `StopTime=0` run, nearly all time should be in initialization.

### Step 3 — Analyze Performance Tracer phases (perfTracer.mat)

Run the `analyzePerfTracer` script:

```matlab
analyzePerfTracer('perfTracer.mat')
```

This parses `PerformanceTracingRawDataVector` using a stack-based approach to match nested start/end phase pairs, and displays a table of all phases with duration and percentage of total wall time.

### Step 4 — Analyze MATLAB Profiler results (profilerResults.mat)

Run the `analyzeProfilerResults` script:

```matlab
analyzeProfilerResults('profilerResults.mat')
```

This computes self time (TotalTime minus children time) for each function, separates shipping code (under `matlabroot`) from user code, and displays two ranked tables:
1. **User files — Top 20 by self time**: Actionable by the user.
2. **Shipping files — Top 20 by self time**: For awareness only.

### Step 5 — Check ModelRefRebuild setting (modelCompileDiary.txt)

Run the `checkModelRefRebuild` script:

```matlab
checkModelRefRebuild('modelCompileDiary.txt')
```

This checks the `ModelRefRebuild` parameter value recorded in the diary:
- **`'IfOutOfDate'`**: Good — recommended value ("If changes in known dependencies detected").
- **`'AssumeUpToDate'`**: Informational — skips all rebuild checks. Fast, but risks stale targets.
- **`'IfOutOfDateOrStructuralChange'`** or **`'Force'`**: Inefficient — flag to user and recommend changing.

### Step 6 — Generate interactive HTML report

Generate a combined HTML report with interactive flamegraphs:

```matlab
generateInitProfilingReport()                        % uses files in current directory
generateInitProfilingReport('path/to/data')          % specify data directory
generateInitProfilingReport('path/to/data', 'report.html')  % specify output path
```

This produces a self-contained HTML file with:
- Summary dashboard (init time, execution time, user vs shipping code split)
- Interactive compile-phase flamegraph (click to zoom, breadcrumb navigation)
- Interactive user-code call tree flamegraph (MathWorks shipping code collapsed)
- Phase table sorted by duration
- User code and shipping code profiler tables
- ModelRefRebuild setting status

To generate only a standalone flamegraph from Performance Tracer data:

```matlab
generateFlamegraph('perfTracer.mat')                 % saves flamegraph_perfTracer.html
generateFlamegraph('perfTracer.mat', 'output.html')  % specify output path
```

### Step 7 — Summarize findings

Present a structured summary with:

1. **Total initialization time** from timing metadata
2. **Phase breakdown** from Performance Tracer (top phases by duration)
3. **Shipping vs user code split** (percentage of self-time in each category)
4. **User-actionable bottlenecks** (top user-code functions by self time, with call counts)
5. **ModelRefRebuild setting** check (flag if not `'IfOutOfDate'`)
6. **Recommendations** prioritized by potential time savings

Focus recommendations on what the user can actually change. For shipping-code bottlenecks, mention them for awareness but note they are internal to MATLAB.
