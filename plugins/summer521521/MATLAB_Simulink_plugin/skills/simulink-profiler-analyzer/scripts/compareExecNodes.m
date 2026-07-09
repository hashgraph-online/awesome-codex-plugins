function compareExecNodes(r1, r2, subsystemName, threshold, label1, label2)
%compareExecNodes  Compare exec-tree nodes for a subsystem across sessions.
%
%   compareExecNodes(r1, r2, subsystemName) compares execution nodes whose
%   ObjectPath contains subsystemName between two profiler sessions. Only
%   nodes with selfTime > 0.001 s in either session are shown.
%
%   compareExecNodes(r1, r2, subsystemName, threshold) uses a custom
%   self-time threshold.
%
%   compareExecNodes(r1, r2, subsystemName, threshold, label1, label2) uses
%   custom labels for each session.
%
%   r1 and r2 are structs returned by parseSimulinkProfilerData.

    arguments
        r1 struct
        r2 struct
        subsystemName (1,1) string
        threshold (1,1) double {mustBeNonnegative} = 0.001
        label1 (1,1) string = "Run1"
        label2 (1,1) string = "Run2"
    end

    % Build a map of key -> selfTime for each run
    map1 = buildExecMap(r1.execTree, subsystemName);
    map2 = buildExecMap(r2.execTree, subsystemName);

    % Merge all keys
    allKeys = unique([keys(map1), keys(map2)]);

    fprintf('\n--- Exec Node Comparison for "%s" (%s vs %s, threshold=%.4f s) ---\n\n', ...
        subsystemName, label1, label2, threshold);
    fprintf('%-50s  %10s  %10s  %8s\n', 'Node', label1+"(s)", label2+"(s)", 'Ratio');
    fprintf('%s\n', repmat('-', 1, 82));

    found = false;
    for i = 1:numel(allKeys)
        k = allKeys(i);
        t1 = 0; t2 = 0;
        if isKey(map1, k), t1 = map1(k); end
        if isKey(map2, k), t2 = map2(k); end

        if t1 < threshold && t2 < threshold
            continue;
        end

        found = true;
        nodeLabel = k;
        if strlength(nodeLabel) > 50
            nodeLabel = "..." + extractAfter(nodeLabel, strlength(nodeLabel) - 47);
        end

        if t1 > 0
            fprintf('%-50s  %10.4f  %10.4f  %8.1fx\n', nodeLabel, t1, t2, t2/t1);
        else
            fprintf('%-50s  %10.4f  %10.4f  %8s\n', nodeLabel, t1, t2, 'new');
        end
    end

    if ~found
        fprintf('  No exec nodes matched "%s" with selfTime > %.4f s in either session.\n', ...
            subsystemName, threshold);
    end
    fprintf('\n');
end

%% ---- Helper: build map of "location | shortPath" -> selfTime ----
function m = buildExecMap(execTree, subsystemName)
    m = containers.Map('KeyType', 'char', 'ValueType', 'double');
    et = execTree;
    for i = 1:height(et)
        obj = strjoin(string(et.ObjectPath{i}), ' > ');
        if ~contains(obj, subsystemName)
            continue;
        end
        loc = string(et.Location(i));
        k = char(loc + " | " + obj);
        if isKey(m, k)
            m(k) = m(k) + et.SelfTime_s(i);
        else
            m(k) = et.SelfTime_s(i);
        end
    end
end
