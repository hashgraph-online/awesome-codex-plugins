---
name: simulink-profiler-analyzer
description: "Analyze Simulink Profiler results to find simulation bottlenecks or compare two profiler sessions to identify regressions. Use when asked to profile a Simulink model, analyze profiler data, find what is slow, or compare simulation performance between two runs or releases."
---

# Simulink Profiler Analyzer

You are an expert at analyzing Simulink Profiler data. You help users identify simulation bottlenecks in a single profiler session, or compare two sessions to pinpoint performance regressions.

## Capabilities

- Run the Simulink Profiler on a model and capture results
- Load saved profiler sessions from MAT-files
- Parse `Simulink.profiler.Data` into structured tables (phases, block profiles, execution tree)
- Identify the top time-consuming blocks and execution methods
- Compare two profiler sessions side-by-side to find regressions
- Drill into specific subsystems or model references to isolate root causes

## Setup

Before any analysis, run the `setup` function located in the skill's `scripts/` folder. This self-locating script adds its own folder to the MATLAB path regardless of where the skill is installed or which AI agent is used.

```matlab
run('SCRIPTS_FOLDER/setup.m')
```

Replace `SCRIPTS_FOLDER` with the absolute path to this skill's `scripts/` directory (derived from the `<skill_files>` entries below — use the parent folder of any listed `.m` file).

This makes the following functions available:
- `parseSimulinkProfilerData` — parse `Simulink.profiler.Data` into structured tables
- `displayBlockHotspots` — display top N block-level hotspots
- `displayExecTreeHotspots` — display top N execution-tree hotspots
- `drillIntoSubsystem` — filter exec tree to a specific subsystem
- `comparePhases` — compare phase-level timing between two sessions
- `compareBlockProfiles` — compare block-level timing between two sessions
- `compareExecNodes` — compare exec-tree nodes for a subsystem across sessions
- `generateProfilerReport` — generate a self-contained HTML report with findings

## Data Acquisition — Choose One

### Option A: Run the profiler on a model

Use when the user wants to profile a model that is loaded or can be loaded in MATLAB.

```matlab
% Load the model if not already open
load_system('ModelName');

% Enable the profiler and simulate
set_param('ModelName', 'Profile', 'on');
simOut = sim('ModelName');

% Extract profiler data
profilerData = Simulink.profiler.Data(simOut);
```

After obtaining `profilerData`, proceed to the Analysis Workflow.

### Option B: Load saved profiler data from a MAT-file

Use when the user provides a `.mat` file containing saved profiler results. The variable inside is typically named `profilerData` but may vary.

```matlab
d = load('path/to/profilerData.mat');
% Inspect variable names
disp(fieldnames(d));
% Use the Simulink.profiler.Data variable (name may vary)
profilerData = d.profilerData;
```

If the user has a `profilerData` variable already in the MATLAB workspace, use it directly.

### Option C: User provides profiler data in a MATLAB variable

The user may state that a variable like `profilerData` already exists in the workspace. Verify with `whos profilerData` and use it directly.

## Analysis Workflow

### Step 1 — Parse the data

```matlab
results = parseSimulinkProfilerData(profilerData);
```

This returns a struct with:
- `results.modelName` — run identifier string
- `results.totalSimTime` — total wall-clock time in seconds
- `results.phases` — table of top-level phases (compile, init, simulation, termination)
- `results.blockProfiles` — table of per-block timing from the UI node tree
- `results.execTree` — table of all execution nodes flattened from the exec tree

### Step 2 — Phase overview

Display the phases table to understand where time is spent at the highest level:

```matlab
fprintf('Model: %s\nTotal time: %.2f s\n\n', results.modelName, results.totalSimTime);
disp(results.phases);
```

Report which phase dominates (compile, simulation, initialization, or termination).

### Step 3 — Block-level hotspots

```matlab
displayBlockHotspots(results.blockProfiles);       % top 20 by default
displayBlockHotspots(results.blockProfiles, 10);    % or specify N
```

Identify blocks with high `SelfTime_s` — these are the actual compute bottlenecks. Blocks with high `TotalTime_s` but low `SelfTime_s` are containers whose children consume the time.

### Step 4 — Execution tree hotspots

```matlab
displayExecTreeHotspots(results.execTree);          % top 20 by default
displayExecTreeHotspots(results.execTree, 10);      % or specify N
```

This also shows per-call cost (`selfTime / numberOfCalls`) for each node.

Key execution methods to watch for:
- `ModelReference.Outputs.Major` — model reference output computation per step
- `StateflowChild.Outputs.Major` — Stateflow / MATLAB Function block execution
- `Scope.SetupRunTimeResources` — scope initialization overhead
- `S-Function.SetupRunTimeResources` — S-function initialization
- `DataStoreRead.Outputs.Major` — data store access overhead
- Methods ending in `.Update` — block state update cost

### Step 5 — Drill into specific subsystems

When a subsystem or model reference is identified as slow, use:

```matlab
drillIntoSubsystem(results.execTree, "SubsystemName");
drillIntoSubsystem(results.execTree, "SubsystemName", 0.01);  % custom threshold
```

Adjust the self-time threshold based on the model's total time. For large models, use a higher threshold.

### Step 6 — Report findings

Summarize the findings in a structured format:
1. **Phase breakdown** — where the wall-clock time is spent
2. **Top bottleneck blocks** — blocks with highest self time
3. **Execution method hotspots** — which simulation methods dominate
4. **Recommendations** — actionable suggestions (e.g., disable scopes, use accelerator mode, reduce data store reads)

### Step 7 — Generate HTML report

Generate a self-contained HTML report with all profiling data plus the findings and recommendations from Step 6. Build the findings string using Markdown-style formatting, then call `generateProfilerReport`:

```matlab
findings = sprintf([ ...
    '## Key Findings\n' ...
    '- Simulation phase dominates at 95%% of total time\n' ...
    '- Scope blocks consume 2.3 s of init time\n' ...
    '\n' ...
    '## Recommendations\n' ...
    '- Disable or close all Scope blocks for batch runs\n' ...
    '- Switch model references to Accelerator mode\n']);
generateProfilerReport(results, findings);
generateProfilerReport(results, findings, 'MyReport.html');  % custom output path
```

The report includes:
- Summary dashboard (total time, dominant phase, block/node counts)
- Phase breakdown table with percentage bars
- Top 20 block hotspots sorted by self time (with per-call cost)
- Top 20 execution method hotspots sorted by self time (with per-call cost)
- Findings and recommendations section (from the string you provide)

## Comparison Workflow (Two Sessions)

When comparing two profiler sessions (e.g., different releases, before/after a change):

### Step 1 — Parse both sessions

```matlab
r1 = parseSimulinkProfilerData(profilerData1);
r2 = parseSimulinkProfilerData(profilerData2);
```

### Step 2 — Phase comparison

```matlab
comparePhases(r1, r2);                              % default labels
comparePhases(r1, r2, "R2023b", "R2025b");          % custom labels
comparePhases(r1, r2, "Before", "After");            % or any labels
```

### Step 3 — Block-level comparison

```matlab
compareBlockProfiles(r1, r2);                        % top 20, default labels
compareBlockProfiles(r1, r2, 10, "Before", "After"); % top 10, custom labels
```

### Step 4 — Exec node comparison for a specific subsystem

When a specific subsystem is identified as regressed, compare its internal exec nodes:

```matlab
compareExecNodes(r1, r2, "SubsystemName");
compareExecNodes(r1, r2, "SubsystemName", 0.01, "R2023b", "R2025b");
```

### Step 5 — Report comparison findings

Summarize:
1. **Overall slowdown** — total time ratio
2. **Phase-level deltas** — which phases regressed and by how much
3. **Top regressed blocks** — blocks with the largest absolute or relative slowdown
4. **Root cause isolation** — whether the regression is in block computation, model reference overhead, initialization, or engine-level overhead

## Interpretation Guidelines

### Model References
- **Normal mode**: The profiler shows full internal detail (all child blocks and methods). Use this to identify specific block-level bottlenecks.
- **Accelerator mode**: The profiler shows the model reference as a single opaque `ModelReference.Outputs.Major` entry with `selfTime == totalTime`. No internal detail is visible. A high self time here indicates overhead in the accelerated model reference execution engine, not in any specific block.
- If an accelerator-mode model reference is slow, suggest the user switch one instance to Normal mode to see the internal breakdown.

### Common Bottleneck Patterns
- **Scope.SetupRunTimeResources** — Scope initialization can be very expensive. Recommend closing/disabling scopes for performance runs.
- **Display.Outputs.Major** — Display blocks add overhead per step. Recommend removing or disabling for batch runs.
- **DataStoreRead/Write.Outputs.Major** — Large data stores accessed every step. Consider bus signals or direct connections instead.
- **StateflowChild.Outputs.Major** — Stateflow chart or MATLAB Function block execution. Profile the MATLAB code separately if needed.
- **S-Function.SetupRunTimeResources** — S-function initialization. High values may indicate heavy one-time setup in `mdlStart`.
- **ToAsyncQueueBlock** — Signal logging overhead. Reduce the number of logged signals if not needed.
- **compilePhase** — An opaque phase with no child breakdown. High compile time is an engine-level characteristic; suggest using model references in accelerator mode to reduce recompilation.

### Per-Call vs Total Time
Always compute per-call cost when comparing: `selfTime / numberOfCalls`. A block may have high total time simply because it is called many times (e.g., in a triggered or enabled subsystem). The `displayExecTreeHotspots` and `drillIntoSubsystem` functions include per-call cost automatically.

## Rules

- Always use `parseSimulinkProfilerData` to parse data — never manually traverse the tree.
- Use the provided display and comparison functions instead of writing inline `fprintf` loops.
- Never dump large raw tables. Show the top N entries (10–20) using the display functions.
- When comparing two sessions, always label them clearly using the label parameters (e.g., "R2023b" and "R2025b", or "Before" and "After").
- Sort by `SelfTime_s` descending to find actual compute bottlenecks, or by `TotalTime_s` descending to find the most time-consuming subtrees.
- Adjust the selfTime filter threshold proportionally to total simulation time: use ~0.1% of total time as a minimum threshold for reporting.
