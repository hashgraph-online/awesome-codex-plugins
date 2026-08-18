function [userFuncs, shipFuncs, userTotal, shipTotal] = parseProfilerData(matFile, topN)
%parseProfilerData Parse MATLAB Profiler results into user vs shipping code.
%
%   [userFuncs, shipFuncs, userTotal, shipTotal] = parseProfilerData(matFile, topN)
%
%   Inputs:
%     matFile - path to .mat file containing profiler results (variable 'p')
%     topN    - number of top functions to return per category (default: 20)
%
%   Outputs:
%     userFuncs - struct array of top user-code functions with fields:
%                 rank, name, selfTime, totalTime, numCalls, file
%     shipFuncs - struct array of top shipping-code functions (same fields)
%     userTotal - total self-time in user code (seconds)
%     shipTotal - total self-time in shipping code (seconds)

    arguments
        matFile (1,1) string = "profilerResults.mat"
        topN (1,1) double {mustBePositive, mustBeInteger} = 20
    end

    S = load(matFile, 'p');
    ft = S.p.FunctionTable;
    mr = matlabroot;
    N = length(ft);

    % Compute self time and classify shipping vs user
    selfTime = zeros(N, 1);
    totalTime = [ft.TotalTime]';
    numCalls = [ft.NumCalls]';
    isShipping = false(N, 1);

    for i = 1:N
        isShipping(i) = startsWith(ft(i).FileName, mr, 'IgnoreCase', true) || isempty(ft(i).FileName);
        childTime = 0;
        if ~isempty(ft(i).Children)
            childTime = sum([ft(i).Children.TotalTime]);
        end
        selfTime(i) = ft(i).TotalTime - childTime;
    end

    [~, idxSelf] = sort(selfTime, 'descend');

    % Extract top user functions
    userFuncs = [];
    k = 0;
    for j = 1:N
        i = idxSelf(j);
        if ~isShipping(i)
            k = k + 1;
            userFuncs(k).rank = k; %#ok<AGROW>
            userFuncs(k).name = ft(i).FunctionName;
            userFuncs(k).selfTime = selfTime(i);
            userFuncs(k).totalTime = totalTime(i);
            userFuncs(k).numCalls = numCalls(i);
            userFuncs(k).file = ft(i).FileName;
            if k >= topN, break; end
        end
    end

    % Extract top shipping functions
    shipFuncs = [];
    k = 0;
    for j = 1:N
        i = idxSelf(j);
        if isShipping(i)
            k = k + 1;
            [~, fname, ext] = fileparts(ft(i).FileName);
            shipFuncs(k).rank = k; %#ok<AGROW>
            shipFuncs(k).name = ft(i).FunctionName;
            shipFuncs(k).selfTime = selfTime(i);
            shipFuncs(k).totalTime = totalTime(i);
            shipFuncs(k).numCalls = numCalls(i);
            shipFuncs(k).file = [fname ext];
            if k >= topN, break; end
        end
    end

    % Totals
    userTotal = sum(selfTime(~isShipping));
    shipTotal = sum(selfTime(isShipping));
end
