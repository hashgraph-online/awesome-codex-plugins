function displayBlockHotspots(blockProfiles, N)
%displayBlockHotspots  Display top N block-level hotspots by total time.
%
%   displayBlockHotspots(blockProfiles) displays the top 20 blocks.
%   displayBlockHotspots(blockProfiles, N) displays the top N blocks.
%
%   blockProfiles is the results.blockProfiles table returned by
%   parseSimulinkProfilerData.

    arguments
        blockProfiles table
        N (1,1) double {mustBePositive, mustBeInteger} = 20
    end

    N = min(N, height(blockProfiles));
    bp = blockProfiles;

    fprintf('\n--- Top %d Blocks by Total Time ---\n\n', N);
    for i = 1:N
        p = bp.Path{i};
        pathStr = strjoin(string(p), ' > ');
        fprintf('%3d) %8.2f s (self %8.2f) calls=%5d  %s\n', ...
            i, bp.TotalTime_s(i), bp.SelfTime_s(i), bp.Calls(i), pathStr);
    end
    fprintf('\n');
end
