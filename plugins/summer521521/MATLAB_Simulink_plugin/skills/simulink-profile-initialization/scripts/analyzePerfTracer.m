function analyzePerfTracer(matFile)
%analyzePerfTracer Parse and display Simulink Performance Tracer phases.
%
%   analyzePerfTracer(matFile) loads the specified .mat file containing
%   PerformanceTracingRawDataVector and displays a table of phase durations.

    if nargin < 1
        matFile = 'perfTracer.mat';
    end

    [phases, ~, totalWall] = parsePerfTracerData(matFile);

    fprintf('\n=== PERFORMANCE TRACER PHASE DURATIONS ===\n');
    fprintf('%-55s %12s  %s\n', 'Phase', 'Duration(s)', '% of Total');
    fprintf('%s\n', repmat('-', 1, 80));
    for k = 1:numel(phases)
        r = phases{k};
        fprintf('%-55s %12.3f  %6.1f%%\n', r.phase, r.duration, r.duration / totalWall * 100);
    end
    fprintf('\nTotal wall time: %.3f s\n', totalWall);
end
