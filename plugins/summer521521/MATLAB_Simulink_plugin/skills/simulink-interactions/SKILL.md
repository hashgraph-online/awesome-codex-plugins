---
name: simulink-interactions
description: Interact with a Simulink model currently open in MATLAB via the MATLAB MCP server. Use this skill whenever the user asks to inspect, modify, query, or navigate a Simulink model that is open in MATLAB — for example changing block properties, finding blocks, adding blocks, connecting signals, or navigating model hierarchy. Trigger whenever the user refers to "this model", "this block", "this subsystem", "selected blocks", or asks to do anything to a Simulink model without specifying a file path to open. Also trigger for requests like "change the gain", "color all sum blocks", "find all integrators", or any other operation on an already-open model.
---

# Simulink Open Model Interaction

This skill defines conventions for interacting with the Simulink model currently open in MATLAB, using `mcp__matlab__evaluate_matlab_code` as the primary tool.

## Tooling Fallback

If the MATLAB MCP tool is unavailable in the current session but the user explicitly asks for real model creation or modification, fall back to local MATLAB execution such as `matlab -batch`. State the fallback briefly and keep the workflow identical: inspect, modify, verify, save.

## Step 1: Resolve References

Before doing anything, determine what model/system/block(s) the user is referring to.

| User says | Resolution |
|---|---|
| "this model" | `bdroot(gcs)` |
| "this system" / "this subsystem" | `gcs` |
| "this block" | `gcb` |
| "selected blocks" (plural) | see snippet below |
| "all [Type] blocks in this subsystem" | see snippet below |
| "all [Type] blocks in the model" | see snippet below |

### Selected blocks (plural)

```matlab
opts = Simulink.FindOptions;
opts.SearchDepth = 1;
blks = getfullname(Simulink.findBlocks(gcs, 'Selected', 'on', opts));
```

### All blocks of a specific type in the current subsystem

```matlab
opts = Simulink.FindOptions;
opts.SearchDepth = 1;
BlockType = 'Gain'; % replace with actual type
blks = getfullname(Simulink.findBlocksOfType(gcs, BlockType, opts));
```

### All blocks of a specific type in the entire model

```matlab
BlockType = 'Gain'; % replace with actual type
blks = getfullname(Simulink.findBlocksOfType(bdroot, BlockType));
```

## Step 2: Inspect Before Modifying

Use `get_param` to read current state before making changes. This helps you confirm you have the right block and understand its current configuration.

```matlab
get_param(gcb, 'Gain')           % read a specific parameter
get_param(gcb,'DialogParameters')  % list all dialog parameters
get_param(gcb, 'ObjectParameters') % list all available parameters
```

## Step 3: Apply Changes

Use `set_param` for most property changes:

```matlab
set_param(gcb, 'Gain', '2')
set_param(gcb, 'BackgroundColor', 'red')
```

For bulk operations on multiple blocks, iterate over the `blks` cell array:

```matlab
for i = 1:numel(blks)
    set_param(blks{i}, 'BackgroundColor', 'yellow');
end
```

## Adding Blocks

When adding blocks, follow these rules:

- **Never** pass a `'Position'` argument to `add_block`
- **Never** use `set_param(blk, 'Position', ...)` or `set_param(blk, 'Location', ...)`
- **Never** use `Simulink.BlockDiagram.arrangeSystem`
- Use `getBlockPosition` and `setBlockDimensions` (bundled in `utils/`) for all positioning
- To read block size, use `getBlockDimensions`; to resize, use `setBlockDimensions`
- Add blocks **one at a time**: add a block, connect it, then position it relative to existing blocks before proceeding to the next

Utility signatures (see `utils/` for full source):
```matlab
[x, y]          = getBlockPosition(block)          % top-left corner
[width, height] = getBlockDimensions(block)         % block size
setBlockPosition(block, x, y)                      % move, preserving size
setBlockDimensions(block, width, height)            % resize, preserving top-left
```

**Never use `set_param(block, 'Position', ...)`** — always use `setBlockPosition` and/or `setBlockDimensions` instead.

```matlab
% Example: add a Gain block to the right of the current block
modelName = bdroot(gcs);
refBlk = gcb;

% 1. Get reference block geometry
[refX, refY] = getBlockPosition(refBlk);
[refW, ~]    = getBlockDimensions(refBlk);

% 2. Add block (no position argument)
newBlk = [modelName '/MyGain'];
add_block('built-in/Gain', newBlk);

% 3. Position it to the right of the reference block
gap = 50;
setBlockPosition(newBlk, refX + refW + gap, refY);

% 4. Connect it
Simulink.connectBlocks(Source,Destination);
```

## Programmatic MATLAB Function Blocks

When editing a MATLAB Function block programmatically, do **not** assume `set_param(block,'Script',...)` exists. For MATLAB Function blocks, update the script through `MATLABFunctionConfiguration`:

```matlab
blk = 'model/MyMATLABFunction';
cfg = get_param(blk, 'MATLABFunctionConfiguration');
cfg.FunctionScript = sprintf([ ...
    'function y = fcn(u)\n' ...
    '%%#codegen\n' ...
    'y = 2*u;\n' ...
    'end\n']);
```

If the function body references workspace parameters such as `Kp`, `tau_sys`, or `Q_max`, explicitly create `Stateflow.Data` entries with `Scope = 'Parameter'` or Simulink may fail size/type inference during compile:

```matlab
rt = sfroot;
machine = rt.find('-isa', 'Stateflow.Machine', 'Name', bdroot(blk));
chart = machine.find('-isa', 'Stateflow.EMChart', 'Path', blk);

param = Stateflow.Data(chart);
param.Name = 'Q_max';
param.Scope = 'Parameter';
```

Without this explicit parameter declaration, a programmatically generated MATLAB Function block can fail with errors like "cannot determine output size/type" even when the same code works interactively.

Common built-in library paths:
- `built-in/Gain`
- `built-in/Product`
- `built-in/Constant`
- `built-in/Scope`
- `built-in/Subsystem`

Exception for Inport and Outport use:
- `sprintf('simulink/Ports &\nSubsystems/In1')`
- `sprintf('simulink/Ports &\nSubsystems/Out1')`

Exception for Sum. Never use the Sum block, always use Add or Subtract instead:
- `sprintf(['simulink/Math\nOperations/Add'])`
- `sprintf(['simulink/Math\nOperations/Subtract'])`

## Connecting Blocks

Always use `Simulink.connectBlocks` to connect blocks — never `add_line`. This API is more robust and handles port resolution automatically.

```matlab
% Connect two blocks (Simulink picks the appropriate ports)
Simulink.connectBlocks(srcBlock, dstBlock);

% Connect specific ports when needed
Simulink.connectBlocks([srcBlock '/1'], [dstBlock '/1']);
```

## Signal Logging

When the user asks to log a signal, use Simulink's built-in signal logging on the port directly. **Never use a To Workspace block or a To File block.**

```matlab
% Log the first output port of a block
ph = get_param(gcb, 'PortHandles');
set(ph.Outport(1), 'DataLogging', 'on');

% Set the name lf the logged signal
set(ph.Outport(1), 'DataLoggingNameMode', 'SignalName');
set(ph.Outport(1), 'Name', 'mySignalName');
```

To log a specific block by path instead of `gcb`:
```matlab
ph = get_param('modelName/BlockName', 'PortHandles');
set(ph.Outport(1), 'DataLogging', 'on');
```

After simulation, logged signals are accessible via `logsout` in the `SimulationOutput` object (when using `sim()`) or via `Simulink.SimulationData.Dataset`.

If the user explicitly asks for `To Workspace` blocks or named workspace artifacts as deliverables, follow the user's request. The "never use To Workspace" rule is only the default when the user asks to log signals and does not constrain the export mechanism.

## Creating Subsystems

When adding a group of related blocks that should live inside a subsystem, add and connect all the blocks first (following the iterative one-at-a-time workflow above), then group them into a subsystem at the end:

```matlab
% Collect handles of all blocks to group
blocks = [get_param('model/Block1', 'Handle'), ...
          get_param('model/Block2', 'Handle'), ...
          get_param('model/Block3', 'Handle')];

% Group into a subsystem — Simulink handles port creation automatically
Simulink.BlockDiagram.createSubsystem(blocks);
```

`createSubsystem` automatically adds the necessary Inport/Outport blocks inside the subsystem and rewires external connections. Do **not** manually create a Subsystem block and move blocks into it.

## Clearing a Subsystem

`Simulink.BlockDiagram.deleteContents` only accepts a block diagram, not an arbitrary subsystem path. If you need to rebuild a subsystem in place, delete its lines and child blocks manually:

```matlab
subsys = 'model/MySubsystem';
lines = find_system(subsys, 'FindAll', 'on', 'SearchDepth', 1, 'Type', 'line');
if ~isempty(lines)
    delete_line(lines);
end

blocks = find_system(subsys, 'SearchDepth', 1, 'Type', 'Block');
blocks = setdiff(blocks, {subsys}, 'stable');
for i = 1:numel(blocks)
    delete_block(blocks{i});
end
```

This is the safe pattern when regenerating subsystem internals from a script.

## Step 4: Verify

After making changes, confirm success by reading back the modified parameter or reporting what was changed.
