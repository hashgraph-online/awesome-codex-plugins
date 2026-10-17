function displayExecTreeHotspots(execTree, N)
%displayExecTreeHotspots  Display top N execution-tree hotspots.
%
%   displayExecTreeHotspots(execTree) displays the top 20 exec nodes.
%   displayExecTreeHotspots(execTree, N) displays the top N exec nodes.
%
%   execTree is the results.execTree table returned by
%   parseSimulinkProfilerData.

    arguments
        execTree table
        N (1,1) double {mustBePositive, mustBeInteger} = 20
    end

    N = min(N, height(execTree));
    et = execTree;

    fprintf('\n--- Top %d Execution Nodes by Total Time ---\n\n', N);
    for i = 1:N
        obj = strjoin(string(et.ObjectPath{i}), ' > ');
        loc = string(et.Location(i));
        perCall = 0;
        if et.Calls(i) > 0
            perCall = et.SelfTime_s(i) / et.Calls(i);
        end
        fprintf('%3d) %8.2f s (self %8.2f, %.4f s/call) calls=%5d  %s [%s]\n', ...
            i, et.TotalTime_s(i), et.SelfTime_s(i), perCall, et.Calls(i), loc, obj);
    end
    fprintf('\n');
end
