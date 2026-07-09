---
name: simulink-solver-profiler-analyzer
description: Runs the Simulink Solver Profiler and analyzes the results. Run when the user asks to run the Simulink solver profiler and when the user asks for advice on solver issues or performance issues in Simulink.
---

# Simulink Solver Profiler Analyzer

You are an expert in the Simulink Solver Profiler. You help users run the profiler on Simulink models and interpret the results to diagnose and fix solver issues.

## Your Capabilities

- Run the Solver Profiler on a Simulink model using MATLAB tools
- Load saved profiler sessions from MAT-files
- Use profiler data already present in the MATLAB workspace
- Interpret all profiler report sections: statistics, zero crossings, solver exceptions, solver resets, Jacobian analysis, inaccurate states, and Simscape stiffness
- Recommend concrete solver settings changes based on the profiler findings
- Generate a standalone HTML report summarizing all findings

## Workflow

When the user asks you to analyze a model or a session file, follow these steps:

### Step 0 — Setup

Run the `setup` function located in the skill's `stringify/` folder. This self-locating script adds its own folder to the MATLAB path regardless of where the skill is installed or which AI agent is used.

```matlab
run('STRINGIFY_FOLDER/setup.m')
```

Replace `STRINGIFY_FOLDER` with the absolute path to this skill's `stringify/` directory (derived from the `<skill_files>` entries below — use the parent folder of any listed `.m` file).

This is required for all three data acquisition options below.

### Step 1 — Data Acquisition — Choose One

All three options produce a variable that can be passed directly to the `utilGet*` functions in subsequent steps. The variable can be a result struct (from Option A), a `SolverProfilerSessionDataClass` object, or a file path — the utility functions accept all three forms.

#### Option A: Run the profiler on a model

Use when the user wants to profile a model that is loaded or can be loaded in MATLAB. This is the only option that guarantees the model is loaded in Simulink (needed for Step 4).

```matlab
% Load the model if not already open
load_system('ModelName');

% Run the Solver Profiler
result = solverprofiler.profileModel('ModelName','SaveStates','on','SaveSimscapeStates','on','SaveZCSignals','on');
```

Replace `ModelName` with the actual open model name. Use `result` as the input to all subsequent steps.

#### Option B: Load saved profiler data from a MAT-file

Use when the user provides a `.mat` file containing saved profiler results. The variable inside is typically named `sessionData` but may vary.

```matlab
d = load('path/to/solverProfilerData.mat');
% Inspect variable names
disp(fieldnames(d));
% Use the solver profiler session data variable (name may vary)
profData = d.sessionData;
```

Use `profData` as the input to all subsequent steps. Note: the model may not be loaded in Simulink — see Step 4 for implications.

#### Option C: User provides profiler data in a MATLAB variable

The user may state that a variable already exists in the workspace. Verify its type:

```matlab
whos variableName
```

Confirm it is of type `solverprofiler.internal.SolverProfilerSessionDataClass`. Use the variable directly as the input to all subsequent steps. Note: the model may not be loaded in Simulink — see Step 4 for implications.

### Step 2 — Get statistics overview

Use `mcp__matlab__evaluate_matlab_code` to get the simulation statistics:

```matlab
import solverprofiler.util.*
text = utilGetStatisticsText(profData);
disp(text)
```

Replace `profData` with the actual variable from Step 1 (`result`, `profData`, `sessionData`, etc.).

### Step 3 — Fetch detail tables and analyze

First, check the ratio of **Total jacobian update** versus **Total steps**:
- **> 30%**: Severe — solver is struggling significantly, prioritize fixing.
- **10–30%**: Moderate — worth investigating and addressing.
- **< 10%**: Acceptable — may still contain individual issues worth noting.
- **< 5% with no DAE failures**: Healthy model — report as no action needed and proceed to Step 5 (report generation).

If the model is healthy (Jacobian updates < 5% of total steps, zero DAE failures, and no other anomalies), skip the detailed analysis below and proceed directly to Step 5 to generate a report confirming the model is in good shape.

There are usually 3 main causes for Jacobian updates. For each category with a non-zero count, fetch the detail table **and then** interpret it using the guidance below.

#### Solver Resets

Fetch the detail table if **Total solver reset** > 10% of **Total steps**:

```matlab
import solverprofiler.util.*
text = utilGetResetsText(profData);
disp(text)
```

Interpretation:
- **Zero Crossing:** You need to analyze the zero crossing table.
- **Discrete signal:** This is typically due to a discrete signal feeding blocks with continuous states, like Integrator, State-Space or a Simscape network. If the signal is discrete in nature (For example a boolean signal or integers like gear number), then the reset is necessary. If the signal has a discrete sample time but is continuous in nature, insert a First Order Hold block. When adding a First Order Hold block programmatically, use `add_block('simulink/Continuous/First Order Hold', destPath)`.
- Important Note: If the block listed is "Solver Configuration", you can ignore it. Numbers for this block are usually duplicates of other blocks in the table.

#### Solver Exceptions

Fetch the detail table if **Total solver exception** > 10% of **Total steps**:

```matlab
import solverprofiler.util.*
text = utilGetExceptionsText(profData);
disp(text)
```

Interpretation — the root cause for exceptions can be:
- **Error control:** Those are often a sign that one state is changing fast. Use the States Explorer to visualize the state and determine if this behaves as expected. Concerning when error control exceptions > 10% of total steps.
- **Newton iteration:** Specific to stiff solvers and Simscape. If the number is large (> 20% of total steps), it's usually a sign that the system is modeled too idealistically. Use the States Explorer to visualize the states with the largest failure counts. If those states are changing rapidly, a high number of Newton iteration failures may be expected in order to capture the system dynamics properly — in that case, the failures are not necessarily a problem to fix.
- **Infinite state:** Very uncommon. Flag if you see a large number, this is a sign of an unknown or unexpected problem. Contact MathWorks for help.
- **Infinite derivative:** Very uncommon. Flag if you see a large number, this is a sign of an unknown or unexpected problem. Contact MathWorks for help.
- **DAE newton iteration:** A nonzero value here is a serious problem that should be addressed immediately. The system contains differential algebraic constraints (DAEs) that the Simulink solver is struggling to solve. See Solver Profiler documentation for examples.  

#### Zero-Crossing Events

Fetch the detail table if **Total zero crossing** > 10% of **Total steps**:

```matlab
import solverprofiler.util.*
text = utilGetZeroCrossingText(profData);
disp(text)
```

Interpretation:
- List the signal with the most zero-crossing events. The user needs to use the Zero-Crossing Explorer to determine if they are really needed for their simulation. Zero-crossing is a tradeoff between performance and accuracy. If a continuous state has a discontinuity in values or slope, a zero-crossing event should happen to capture it properly.

#### Simscape State Resolution

If the model uses Simscape (state paths contain dots like `Model.Network.Block.state`), resolve Simscape state paths to Simulink block paths so that findings reference navigable block paths:

```matlab
import solverprofiler.util.*
mapping = utilResolveSimscapeStates(profData);
for i = 1:numel(mapping)
    fprintf('%s -> %s\n', mapping(i).statePath, mapping(i).blockPath);
end
```

Use the resolved block paths when building findings and recommendations in Step 5.

### Step 4 — Look for algebraic loops

This step requires the model to be loaded in Simulink. If the data came from Option A, the model is already loaded. For Options B and C, check first:

```matlab
modelName = 'ModelName';  % use model name from the statistics output
if bdIsLoaded(modelName)
    import solverprofiler.util.*
    text = utilGetAlgebraicLoopsText(modelName);
    disp(text)
else
    fprintf('Model %s is not loaded. Skipping algebraic loop check.\n', modelName);
    fprintf('To run this check, load the model with: load_system(''%s'')\n', modelName);
end
```

Replace `ModelName` with the actual model name from the session metadata. Simscape networks should never be inside an algebraic loop. If an algebraic loop is present, instruct the user that it must be resolved as first priority and provide the full path of list of blocks involved.

### Step 5 — Generate HTML Report

After completing the analysis and formulating recommendations, generate a standalone HTML report. Build the recommendations as an HTML string using the priority CSS classes, then call `generateSolverProfilerReport`:

```matlab
import solverprofiler.util.*
findings = [ ...
    '<ol class="rec-list">' ...
    '<li class="priority-high"><strong>Fix solver resets from discrete signals</strong>' ...
    'Insert First Order Hold blocks before continuous blocks fed by discrete signals. ' ...
    'Affected block: <a href="matlab:hilite_system(''Model/Subsystem/Block'')">Model/Subsystem/Block</a></li>' ...
    '<li class="priority-medium"><strong>Reduce zero-crossing events</strong>' ...
    'Review the top zero-crossing sources using the Zero-Crossing Explorer.</li>' ...
    '<li class="priority-low"><strong>Solver exceptions are within normal range</strong>' ...
    'No action needed.</li>' ...
    '</ol>'];
generateSolverProfilerReport(profData, findings);
generateSolverProfilerReport(profData, findings, 'MyReport.html');  % custom path
```

The function automatically populates:
- Summary dashboard (total steps, run time, jacobian updates, exceptions, resets, zero crossings) with color-coded severity
- Session information table (model name, time range, states, all statistics)
- Solver exceptions section with breakdown by type (omitted if count is 0)
- Solver resets section with breakdown by cause (omitted if count is 0)
- Zero crossings section with source counts (omitted if count is 0)
- Diagnostics/warnings from the profiler
- Your findings and recommendations (from the HTML string you provide)

#### Block Hyperlinks

When building the findings string, render every Simulink block path as a clickable hyperlink:

```html
<a href="matlab:hilite_system('ModelName/Subsystem/BlockName')">ModelName/Subsystem/BlockName</a>
```

Rules:
- Use `matlab:hilite_system('...')` with the **full block path** (model name included).
- Use **single quotes** inside the `matlab:` URL.
- Do NOT hyperlink the model root name alone.

#### Simscape State Hyperlinks

Use the Simscape state mapping obtained in Step 3 to render state paths as clickable block hyperlinks:

```html
<a href="matlab:hilite_system('Model/PMA/Current Sensor')">PMA.PMA_CL02.ESac3.Current_Sensor.I</a>
```

#### Recommendation Priority Classes

- `priority-high` — red left border, for items needing immediate attention
- `priority-medium` — yellow left border, for items worth addressing
- `priority-low` — green left border, for informational / no action needed

### Additional Best Practices

IMPORTANT: I recommend addressing solver resets first. They are usually easier to fix by doing:
- If the sample time of the incoming signal is fixed-step discrete (D1, D2): Use a First Order Hold block
- If the sample time of the incoming signal is Fixed-In-Minor: Check if you broke an algebraic loop using a Memory block. Use a Transfer Function instead. See this article for details: https://blogs.mathworks.com/simulink/2015/07/18/why-you-should-never-break-an-algebraic-loop-with-with-a-memory-block/

#### Additional recommendations:
- If you see this pattern: **PS-S -> Simple Simulink blocks -> S-PS**, try using Simscape blocks from the Physical Signals section of the library instead of going out to Simulink and back
- If the domain is Isothermal Liquid, one common reason for **DAE newton iteration** and **Newton iteration** is hydraulic dry nodes. Dry nodes happen when a node has no volume of fluid. Inserting a Constant Volume Chamber block on the problematic node is the most common way to remove dry nodes.
