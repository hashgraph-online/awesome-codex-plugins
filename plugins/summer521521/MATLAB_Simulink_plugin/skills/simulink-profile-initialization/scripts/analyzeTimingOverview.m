function analyzeTimingOverview(matFile)
%analyzeTimingOverview Display timing overview from a SimulationOutput MAT-file.
%
%   analyzeTimingOverview() loads 'out_after.mat' from the current directory.
%   analyzeTimingOverview(matFile) loads the specified MAT-file.
%
%   Displays the breakdown of wall time between initialization, execution,
%   and termination phases.

    arguments
        matFile (1,1) string = "out_after.mat"
    end

    S = load(matFile, 'out');
    ti = S.out.SimulationMetadata.TimingInfo;

    total = ti.TotalElapsedWallTime;
    init  = ti.InitializationElapsedWallTime;
    exec  = ti.ExecutionElapsedWallTime;
    term  = ti.TerminationElapsedWallTime;

    fprintf('\n=== TIMING OVERVIEW ===\n');
    fprintf('Start:          %s\n', ti.WallClockTimestampStart);
    fprintf('Stop:           %s\n', ti.WallClockTimestampStop);
    fprintf('Total wall time: %.2f s\n\n', total);
    fprintf('  %-20s %8.2f s  (%5.1f%%)\n', 'Initialization', init, init/total*100);
    fprintf('  %-20s %8.2f s  (%5.1f%%)\n', 'Execution',      exec, exec/total*100);
    fprintf('  %-20s %8.2f s  (%5.1f%%)\n', 'Termination',    term, term/total*100);
    fprintf('\n');
end
