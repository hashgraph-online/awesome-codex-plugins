function collectInitProfiling(mdl)
%collectInitProfiling Profile the initialization phase of a Simulink model.
%   collectInitProfiling(mdl) profiles the compile/init phase of the
%   specified model by simulating with StopTime=0. If mdl is not provided,
%   bdroot is used.
%
%   Produces four files in the current directory:
%     out_after.mat          - SimulationOutput with timing metadata
%     profilerResults.mat    - MATLAB Profiler results (variable p)
%     perfTracer.mat         - Simulink Performance Tracer raw data
%     modelCompileDiary.txt  - Command window diary
%
%   Also creates a timestamped .zip archive of all four files.

    if nargin < 1
        mdl = bdroot;
    end

    PerfTools.Tracer.enable('All Simulink Compile', true);
    PerfTools.Tracer.clearRawData();
    profile on -historysize 50000000
    diary modelCompileDiary.txt
    ModelRefRebuild = get_param(mdl, 'UpdateModelReferenceTargets') %#ok<NOPRT>
    out = sim(mdl, 'StopTime', '0', 'CaptureErrors', 'on');
    diary off
    p = profile('info');
    save profilerResults p
    PerfTools.Tracer.saveToFile('perfTracer.mat')
    save out_after out
    PerfTools.Tracer.enable('All Simulink Compile', false);
    zip(['PerfData-' char(datetime("now", 'Format', "uuuuMMdd'T'HHmmss")) '.zip'], ...
        {'out_after.mat', 'perfTracer.mat', 'profilerResults.mat', 'modelCompileDiary.txt'});
end
