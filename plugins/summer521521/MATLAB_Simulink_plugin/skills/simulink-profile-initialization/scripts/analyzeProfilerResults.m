function analyzeProfilerResults(matFile, topN)
%analyzeProfilerResults Parse MATLAB Profiler results and separate user vs shipping code.
%
%   analyzeProfilerResults(matFile, topN) loads profiler results from matFile
%   (default: 'profilerResults.mat') and displays the top topN (default: 20)
%   functions by self time, separated into user files and MATLAB shipping files.

    if nargin < 1
        matFile = 'profilerResults.mat';
    end
    if nargin < 2
        topN = 20;
    end

    [userFuncs, shipFuncs, userTotal, shipTotal] = parseProfilerData(matFile, topN);

    % --- User files ---
    fprintf('\n=== USER FILES — TOP %d BY SELF TIME ===\n', topN);
    fprintf('%-4s %-10s %-10s %-10s %-50s %s\n', 'Rank', 'SelfTime', 'TotalTime', 'NumCalls', 'FunctionName', 'File');
    fprintf('%s\n', repmat('-', 1, 150));
    for k = 1:numel(userFuncs)
        f = userFuncs(k);
        fprintf('%-4d %-10.3f %-10.3f %-10d %-50s %s\n', ...
            f.rank, f.selfTime, f.totalTime, f.numCalls, f.name, f.file);
    end

    % --- Shipping files ---
    fprintf('\n=== SHIPPING FILES — TOP %d BY SELF TIME ===\n', topN);
    fprintf('%-4s %-10s %-10s %-10s %-50s %s\n', 'Rank', 'SelfTime', 'TotalTime', 'NumCalls', 'FunctionName', 'File');
    fprintf('%s\n', repmat('-', 1, 150));
    for k = 1:numel(shipFuncs)
        f = shipFuncs(k);
        fprintf('%-4d %-10.3f %-10.3f %-10d %-50s %s\n', ...
            f.rank, f.selfTime, f.totalTime, f.numCalls, f.name, f.file);
    end

    % --- Totals ---
    fprintf('\nTotal self-time in USER files:     %.3f s\n', userTotal);
    fprintf('Total self-time in SHIPPING files: %.3f s\n', shipTotal);
    fprintf('Grand total self-time:             %.3f s\n', userTotal + shipTotal);
end
