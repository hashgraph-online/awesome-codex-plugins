function results = parseSimulinkProfilerData(profilerData)
%parseSimulinkProfilerData  Parse Simulink.profiler.Data into tables.
%
%   results = parseSimulinkProfilerData(profilerData) parses a
%   Simulink.profiler.Data object and returns a struct with:
%
%     results.modelName      - Name/run identifier string
%     results.totalSimTime   - Total wall-clock time (seconds)
%     results.phases         - Table of top-level simulation phases
%     results.blockProfiles  - Table of per-block timing (from UI tree)
%     results.execTree       - Table of all execution nodes (flattened)
%
%   The output tables are self-contained and can be sorted, filtered, or
%   exported with writetable/writetimetable.
%
%   Example:
%     profilerData = Simulink.profiler.Data.loadobj(load('profData.mat'));
%     results = parseSimulinkProfilerData(profilerData);
%     disp(results.phases);
%     disp(sortrows(results.blockProfiles, 'TotalTime_s', 'descend'));

    arguments
        profilerData (1,1) Simulink.profiler.Data
    end

    %% Meta information
    results.modelName    = string(profilerData.run);
    results.totalSimTime = profilerData.rootExecNode.totalTime;

    %% 1. Top-level phases from rootExecNode children
    re = profilerData.rootExecNode;
    nPhases = numel(re.children);
    phaseName   = strings(nPhases, 1);
    phaseTotal  = zeros(nPhases, 1);
    phaseSelf   = zeros(nPhases, 1);
    phaseCalls  = zeros(nPhases, 1);
    phasePct    = zeros(nPhases, 1);
    for k = 1:nPhases
        c = re.children(k);
        phaseName(k)  = string(c.location);
        phaseTotal(k) = c.totalTime;
        phaseSelf(k)  = c.selfTime;
        phaseCalls(k) = c.numberOfCalls;
        phasePct(k)   = c.totalTime / results.totalSimTime * 100;
    end
    results.phases = table(phaseName, phaseTotal, phaseSelf, phaseCalls, phasePct, ...
        'VariableNames', {'Phase','TotalTime_s','SelfTime_s','Calls','PctOfTotal'});
    results.phases = sortrows(results.phases, 'TotalTime_s', 'descend');

    %% 2. Per-block profiles from UINode tree (recursive)
    blockData = flattenUINode(profilerData.rootUINode, 0);
    results.blockProfiles = struct2table(blockData);
    results.blockProfiles = sortrows(results.blockProfiles, 'TotalTime_s', 'descend');

    %% 3. Flattened execution-node tree from rootExecNode (recursive)
    execData = flattenExecNode(profilerData.rootExecNode, 0);
    results.execTree = struct2table(execData);
    results.execTree = sortrows(results.execTree, 'TotalTime_s', 'descend');
end

%% ---- Helper: recursively flatten UINode tree ----
function rows = flattenUINode(node, depth)
    rows = struct( ...
        'Path',        string(node.path), ...
        'Depth',       depth, ...
        'TotalTime_s', node.totalTime, ...
        'SelfTime_s',  node.selfTime, ...
        'Calls',       node.numberOfCalls, ...
        'NumExecNodes', numel(node.execNodes));

    for k = 1:numel(node.children)
        childRows = flattenUINode(node.children(k), depth + 1);
        rows = [rows; childRows]; %#ok<AGROW>
    end
end

%% ---- Helper: recursively flatten ExecNode tree ----
function rows = flattenExecNode(node, depth)
    rows = struct( ...
        'Location',    string(node.location), ...
        'ObjectPath',  string(node.objectPath), ...
        'Depth',       depth, ...
        'TotalTime_s', node.totalTime, ...
        'SelfTime_s',  node.selfTime, ...
        'Calls',       node.numberOfCalls);

    for k = 1:numel(node.children)
        childRows = flattenExecNode(node.children(k), depth + 1);
        rows = [rows; childRows]; %#ok<AGROW>
    end
end
