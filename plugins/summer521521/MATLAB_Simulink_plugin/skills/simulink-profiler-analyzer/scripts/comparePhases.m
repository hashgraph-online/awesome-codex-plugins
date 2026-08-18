function comparePhases(r1, r2, label1, label2)
%comparePhases  Compare phase-level timing between two profiler sessions.
%
%   comparePhases(r1, r2) compares phases using labels "Run1" and "Run2".
%   comparePhases(r1, r2, label1, label2) uses custom labels (e.g.,
%   "R2023b", "R2025b" or "Before", "After").
%
%   r1 and r2 are structs returned by parseSimulinkProfilerData.

    arguments
        r1 struct
        r2 struct
        label1 (1,1) string = "Run1"
        label2 (1,1) string = "Run2"
    end

    fprintf('\n--- Phase Comparison: %s vs %s ---\n', label1, label2);
    fprintf('Total time: %s = %.2f s, %s = %.2f s (%.1fx)\n\n', ...
        label1, r1.totalSimTime, label2, r2.totalSimTime, r2.totalSimTime / r1.totalSimTime);

    phases = outerjoin(r1.phases, r2.phases, 'Keys', 'Phase', 'MergeKeys', true);

    fmt = '%-22s  %10s  %10s  %8s\n';
    fprintf(fmt, 'Phase', label1 + "(s)", label2 + "(s)", 'Ratio');
    fprintf('%s\n', repmat('-', 1, 55));

    for i = 1:height(phases)
        t1 = phases.TotalTime_s_r1(i);
        t2 = phases.TotalTime_s_r2(i);
        if isnan(t1), t1 = 0; end
        if isnan(t2), t2 = 0; end
        if t1 > 0
            fprintf('%-22s  %10.2f  %10.2f  %8.1fx\n', phases.Phase(i), t1, t2, t2/t1);
        else
            fprintf('%-22s  %10.2f  %10.2f  %8s\n', phases.Phase(i), t1, t2, 'new');
        end
    end
    fprintf('\n');
end
