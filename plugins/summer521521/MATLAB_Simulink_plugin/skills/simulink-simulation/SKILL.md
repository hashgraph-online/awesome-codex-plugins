---
name: simulink-simulation
description: Use this skill whenever simulating a Simulink model, running the sim command, setting up SimulationInput objects, passing input signals via timeseries or datasets, configuring model or block parameters programmatically, or accessing logged output data from SimulationOutput. Trigger for any request involving sim(), Simulink.SimulationInput, Simulink.SimulationOutput, logsout, setExternalInput, or setModelParameter.
---

# Simulating Simulink Models with the sim Command

## Minimal working pattern

Always simulate using `Simulink.SimulationInput` and `Simulink.SimulationOutput`:

```matlab
in = Simulink.SimulationInput('MyModel');
in = in.setModelParameter('StopTime', '10');
out = sim(in);
```

Never use `set_param`, `load_system`, or `open_system` to drive simulation — the `SimulationInput` API replaces all of these.

If the MATLAB MCP tool is unavailable but the user explicitly asks for real artifacts such as `.slx`, exported figures, or `.mat` results, use local MATLAB execution such as `matlab -batch` as a fallback. Give MATLAB generous timeouts because startup alone can take minutes.

For MATLAB MCP core server v0.9.0 and newer, this personal plugin launcher can pass through optional session/logging settings via environment variables:
- `MATLAB_SESSION_MODE` -> `--matlab-session-mode`
- `MATLAB_EXTENSION_FILE` -> `--extension-file`
- `MATLAB_EXTENSION_FILES` -> repeated `--extension-file` values, separated by the OS path separator (`;` on Windows)
- `MATLAB_LOG_FOLDER` -> `--log-folder`
- `MATLAB_LOG_LEVEL` -> `--log-level`

MATLAB MCP core server v0.9.2 improves `--initialize-matlab-on-startup=true` so the MCP server is not blocked while MATLAB starts, and fixes `shareMATLABSession()` failures on Windows. Keep the launcher default lazy startup unless the user explicitly wants startup-time initialization.

MATLAB MCP core server v0.10.0 makes `auto` the default session mode. Leave `MATLAB_SESSION_MODE` unset for normal use, set it to `existing` only when the user has run `shareMATLABSession()` in the target MATLAB session, and use multiple extension files only when the current MCP server exposes those custom tools.

Keep `MATLAB_SETUP_MATLAB` unset for normal MCP sessions; set it only for a one-time upstream setup run.

## Setting parameters

Use `SimulationInput` methods to configure the simulation:

```matlab
% Model-level parameters (StopTime, SolverType, SimulationMode, etc.)
in = in.setModelParameter('StopTime', '10', 'SolverType', 'Fixed-step');

% Block parameters
in = in.setBlockParameter('MyModel/Gain', 'Gain', '5');

% MATLAB workspace variables used by the model
in = in.setVariable('Kp', 1.2);
```

## Input signals

Pass input signals through Inport blocks using a `Simulink.SimulationData.Dataset`. Each timeseries `Name` must match the corresponding Inport block's signal name, otherwise the signal won't be routed correctly.

```matlab
dt = 0.01; % sample time
N = 1000; % Number of points
t = dt*(0:N)';
u = sin(2*pi*t);

ts = timeseries(u, t);
ts.Name = 'mySignal';   % must match the Inport signal name in the model

ds = Simulink.SimulationData.Dataset;
ds{1} = ts;

in = in.setExternalInput(ds);
out = sim(in);
```

## Discovering logged signals

Before accessing logged data by name, discover what signals the model actually logs by running a simulation and inspecting `logsout`:

```matlab
in = Simulink.SimulationInput('MyModel');
out = sim(in);
disp('List of logged signals:');
disp(out.logsout.getElementNames);
```

This is especially useful when working with an unfamiliar model — the names returned here are exactly the names to use when calling `out.logsout.get(...)`.

## Accessing logged data

Logged signals are available through `out.logsout`. Access them directly by name — no intermediate variables needed:

```matlab
% Plot a logged signal
plot(out.logsout.get('signalName').Values)

% Get time and data separately
sig = out.logsout.get('signalName').Values;
plot(sig.Time, sig.Data)
```

Do not validate `out` with try-catch or `isfield` — `sim` either returns a valid `SimulationOutput` or throws an error. `Simulink.SimulationOutput` has no `isfield` method.

## Accessing To Workspace Outputs

If the model uses `To Workspace` blocks and `ReturnWorkspaceOutputs` is on, retrieve those outputs directly from the `SimulationOutput` object:

```matlab
in = Simulink.SimulationInput('MyModel');
in = in.setModelParameter('ReturnWorkspaceOutputs', 'on');
out = sim(in);

T = out.simout_T;
Q = out.simout_Qbase;
```

Normalize the exported value before post-processing because `To Workspace` may return a `timeseries`, a `Simulink.SimulationData.Signal`, or a numeric matrix depending on block settings:

```matlab
if isa(T, 'timeseries')
    t = T.Time(:);
    y = T.Data(:);
elseif isa(T, 'Simulink.SimulationData.Signal')
    t = T.Values.Time(:);
    y = T.Values.Data(:);
else
    t = T(:,1);
    y = T(:,2);
end
```

## Multiple simulations

When running many simulations, create an array of `Simulink.SimulationInput` objects using the `repmat` function instead of looping over `sim`:

```matlab
in = repmat(Simulink.SimulationInput('MyModel'),N,1);
for k = 1:N
    in(k) = Simulink.SimulationInput('MyModel');
    in(k) = in(k).setVariable('gain', gains(k));
end
out = sim(in);
```

When collecting results from multiple cases into a struct array, preallocate a homogeneous struct shape before the loop. MATLAB will throw "subscripted assignment between dissimilar structures" if later cases add fields or nested layouts that the first element did not have.

## Parallel simulation (parsim)

To run multiple simulations, use `parsim` instead of looping over `sim`:

```matlab
for k = 1:N
    in(k) = Simulink.SimulationInput('MyModel');
    in(k) = in(k).setVariable('gain', gains(k));
end
out = parsim(in);
```

## Rebuild-and-Simulate Pitfalls

If a script repeatedly rebuilds and reruns a model:

- Save or clear the dirty flag before `close_system`, otherwise MATLAB can warn that the changed model cannot be closed.
- Avoid model names that shadow scripts or functions on the MATLAB path; model/script name collisions can produce confusing warnings during `sim` and `run`.
- When a generated model relies on MATLAB Function blocks with workspace parameters, make sure those symbols are declared as block parameters during model construction; otherwise simulation can fail before `sim` starts with output-size/type inference errors.
