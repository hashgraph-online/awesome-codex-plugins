---
name: simulink-baseline-test
description: Create a MATLAB baseline regression test class for a Simulink model. Use when asked to create a baseline test, golden-reference test, or regression test for a Simulink model.
---

# Simulink Baseline Test Creation

Creates a MATLAB test class that captures and validates Simulink model outputs against a saved baseline.

## Workflow

### Step 1: Analyze the Model

Resolve the model name and explore its structure to select 2–5 signals representative of the model's key behavior.

```matlab
modelName = bdroot(gcs);

% List top-level subsystems
opts = Simulink.FindOptions;
opts.SearchDepth = 1;
topBlocks = getfullname(Simulink.findBlocks(modelName, opts));
for i = 1:numel(topBlocks)
    bt = get_param(topBlocks{i}, 'BlockType');
    fprintf('  [%s] %s\n', bt, topBlocks{i});
end
```

Explore subsystem ports, bus selectors, scopes, and outports to understand signal flow. Look for signals that best represent the model's overall behavior — plant outputs, actuator commands, sensor readings, or any other meaningful quantities.

### Step 2: Configure Signal Logging

Enable logging on selected output ports:

```matlab
ph = get_param('<block path>', 'PortHandles');
set(ph.Outport(1), 'DataLogging', 'on');
set(ph.Outport(1), 'Name', '<signalName>');
```

**Never** use To Workspace blocks for signal capture.

### Step 3: Capture Baseline

Simulate and save the full `logsout` Dataset — not individual timeseries:

```matlab
in = Simulink.SimulationInput(modelName);
out = sim(in);

baselineLogsout = out.logsout;
save(fullfile(modelDir, 'baselineData.mat'), 'baselineLogsout');
```

### Step 4: Write the Test Class

Follow these mandatory conventions:

#### Inherit from `sltest.TestCase`

```matlab
classdef MyModelBaselineTest < sltest.TestCase
```

Not `matlab.unittest.TestCase`. This gives access to `verifySignalsMatch`.

#### Single simulation, single comparison

Simulate the model **once**. Compare **all** signals in one call using `verifySignalsMatch`:

```matlab
testCase.verifySignalsMatch(out.logsout, S.baselineLogsout, ...
    'RelTol', testCase.RelTol, ...
    'AbsTol', testCase.AbsTol);
```

**Never** loop through individual signals. **Never** simulate once per signal.

#### Use `RelTol` and `AbsTol` directly

Pass `'RelTol'` and `'AbsTol'` as name-value arguments. MATLAB applies `RelTol` element-wise per sample; `AbsTol` acts as a floor for values near zero. **Never** manually scale tolerances (e.g., `max(abs(data)) * relTol`).

#### Smart model teardown with `bdIsLoaded`

Only close the model if it was not already loaded before the test:

```matlab
wasLoaded = bdIsLoaded(testCase.ModelName);
load_system(testCase.ModelName);
if ~wasLoaded
    testCase.addTeardown(@()close_system(testCase.ModelName, 0));
end
```

#### Do NOT manually run `PreLoadFcn`

`load_system` automatically triggers the model's `PreLoadFcn` callback. Never call `evalin('base', get_param(model, 'PreLoadFcn'))`.

#### Include a static `generateBaseline()` method

For easy re-baselining after intentional changes:

```matlab
methods (Static)
    function generateBaseline()
        modelName = MyModelBaselineTest.ModelName;
        load_system(modelName);
        in = Simulink.SimulationInput(modelName);
        out = sim(in);
        baselineLogsout = out.logsout; %#ok<NASGU>
        save(MyModelBaselineTest.BaselineFile, 'baselineLogsout');
        close_system(modelName, 0);
    end
end
```

### Step 5: Run and Verify

Execute the test and confirm all signals match:

```matlab
results = runtests('MyModelBaselineTest');
```

## Complete Test Class Template

```matlab
classdef MyModelBaselineTest < sltest.TestCase

    properties (Constant)
        ModelName    = 'MyModel'
        BaselineFile = fullfile(fileparts(mfilename('fullpath')), 'baselineData.mat')
        RelTol = 1e-6
        AbsTol = 1e-8
    end

    methods (TestClassSetup)
        function loadModelAndBaseline(testCase)
            wasLoaded = bdIsLoaded(testCase.ModelName);
            load_system(testCase.ModelName);
            if ~wasLoaded
                testCase.addTeardown(@()close_system(testCase.ModelName, 0));
            end

            testCase.assertTrue(isfile(testCase.BaselineFile), ...
                sprintf('Baseline not found: %s\nRun %s.generateBaseline() first.', ...
                testCase.BaselineFile, mfilename('class')));
        end
    end

    methods (Test)
        function testAllSignalsMatchBaseline(testCase)
            in  = Simulink.SimulationInput(testCase.ModelName);
            out = sim(in);

            S = load(testCase.BaselineFile, 'baselineLogsout');

            testCase.verifySignalsMatch(out.logsout, S.baselineLogsout, ...
                'RelTol', testCase.RelTol, ...
                'AbsTol', testCase.AbsTol);
        end
    end

    methods (Static)
        function generateBaseline()
            modelName = MyModelBaselineTest.ModelName;
            load_system(modelName);

            in  = Simulink.SimulationInput(modelName);
            out = sim(in);

            baselineLogsout = out.logsout; %#ok<NASGU>
            save(MyModelBaselineTest.BaselineFile, 'baselineLogsout');
            fprintf('Baseline saved to: %s\n', MyModelBaselineTest.BaselineFile);

            close_system(modelName, 0);
        end
    end
end
```

## Anti-Patterns — Do NOT

- **Simulate once per signal** (parameterized tests calling `sim` each time)
- **Loop through signals** to verify individually — use `verifySignalsMatch`
- **Manually scale tolerances** (`max(abs(data)) * relTol`) — use `'RelTol'` directly
- **Save individual timeseries** — save the full `logsout` Dataset
- **Unconditionally close the model** — check `bdIsLoaded` first
- **Manually call `PreLoadFcn`** — `load_system` handles it
- **Use `matlab.unittest.TestCase`** — use `sltest.TestCase` for `verifySignalsMatch`
