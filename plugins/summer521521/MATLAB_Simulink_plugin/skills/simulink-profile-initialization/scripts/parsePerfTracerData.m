function [phases, flamegraphJson, totalWall] = parsePerfTracerData(matFile)
%parsePerfTracerData Parse Performance Tracer data into phases and flamegraph JSON.
%
%   [phases, flamegraphJson, totalWall] = parsePerfTracerData(matFile)
%
%   Inputs:
%     matFile - path to .mat file containing PerformanceTracingRawDataVector
%
%   Outputs:
%     phases         - cell array of structs with fields: phase, duration, startIdx
%                      sorted by original occurrence order
%     flamegraphJson - JSON string of the hierarchical flamegraph tree
%     totalWall      - total wall-clock time in seconds

    arguments
        matFile (1,1) string = "perfTracer.mat"
    end

    S = load(matFile, 'PerformanceTracingRawDataVector');
    data = S.PerformanceTracingRawDataVector;
    N = numel(data);

    % Extract timestamps
    timestamps = zeros(N, 1);
    for i = 1:N
        timestamps(i) = data{i}{10};
    end
    baseTime = timestamps(1);
    totalWall = timestamps(end) - baseTime;

    % --- Flat results (for table display) ---
    stack = {};
    results = {};
    for i = 1:N
        e = data{i};
        phase = e{3};
        isStart = e{9};
        ts = e{10};

        if isStart
            stack{end+1} = struct('phase', phase, 'startTime', ts, 'startIdx', i); %#ok<AGROW>
        else
            for s = numel(stack):-1:1
                if strcmp(stack{s}.phase, phase)
                    dur = ts - stack{s}.startTime;
                    results{end+1} = struct('phase', phase, 'duration', dur, 'startIdx', stack{s}.startIdx); %#ok<AGROW>
                    stack(s) = [];
                    break;
                end
            end
        end
    end

    % Sort by original occurrence
    startIdxs = cellfun(@(r) r.startIdx, results);
    [~, order] = sort(startIdxs);
    phases = results(order);

    % --- Hierarchical tree (for flamegraph) ---
    root = struct('name', 'Total', 'start', 0, 'duration', totalWall, 'children', {{}});
    treeStack = {root};
    for i = 1:N
        e = data{i};
        phase = e{3};
        isStart = e{9};
        ts = e{10};
        t = ts - baseTime;

        if isStart
            node = struct('name', phase, 'start', t, 'duration', 0, 'children', {{}});
            treeStack{end+1} = node; %#ok<AGROW>
        else
            for s = numel(treeStack):-1:2
                if strcmp(treeStack{s}.name, phase)
                    finished = treeStack{s};
                    finished.duration = t - finished.start;
                    treeStack(s) = [];
                    parent = treeStack{end};
                    parent.children{end+1} = finished;
                    treeStack{end} = parent;
                    break;
                end
            end
        end
    end
    root = treeStack{1};
    flamegraphJson = node2json(root);
end
