function compareBlockProfiles(r1, r2, N, label1, label2)
%compareBlockProfiles  Compare block-level timing between two sessions.
%
%   compareBlockProfiles(r1, r2) compares the top 20 blocks from r2 against
%   matching blocks in r1.
%
%   compareBlockProfiles(r1, r2, N) limits the output to the top N blocks.
%
%   compareBlockProfiles(r1, r2, N, label1, label2) uses custom labels.
%
%   r1 and r2 are structs returned by parseSimulinkProfilerData.

    arguments
        r1 struct
        r2 struct
        N (1,1) double {mustBePositive, mustBeInteger} = 20
        label1 (1,1) string = "Run1"
        label2 (1,1) string = "Run2"
    end

    bp1 = r1.blockProfiles;
    bp2 = r2.blockProfiles;
    N = min(N, height(bp2));

    fprintf('\n--- Top %d Block Regressions (%s → %s, by SelfTime) ---\n\n', N, label1, label2);

    for i = 1:N
        p = bp2.Path{i};
        pathStr = strjoin(string(p), ' > ');

        % Find matching block in the other session by path
        matchIdx = find(cellfun(@(x) isequal(string(x), string(p)), bp1.Path), 1);

        if ~isempty(matchIdx)
            t1 = bp1.SelfTime_s(matchIdx);
            t2 = bp2.SelfTime_s(i);
            if t1 > 0
                fprintf('%8.2f → %8.2f s (%5.1fx)  %s\n', t1, t2, t2/t1, pathStr);
            else
                fprintf('%8.2f → %8.2f s (%8s)  %s\n', t1, t2, 'new', pathStr);
            end
        else
            fprintf('%8s → %8.2f s (%8s)  %s\n', 'N/A', bp2.SelfTime_s(i), 'new', pathStr);
        end
    end
    fprintf('\n');
end
