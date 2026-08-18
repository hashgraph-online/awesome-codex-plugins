% Copyright 2026 The MathWorks, Inc.
function text = utilFormatStatisticsAsText(reportData)
%UTILFORMATSTATISTICSASTEXT Format session information and simulation statistics as plain text
%
% Takes the structured reportData from utilExtractReportData and formats
% only the session information and simulation statistics as readable text.

    import solverprofiler.util.*

    parts = {};

    % === HEADER ===
    parts{end+1} = '==========================================================';
    parts{end+1} = 'SOLVER PROFILER REPORT';
    parts{end+1} = '==========================================================';
    parts{end+1} = '';

    % === METADATA ===
    parts{end+1} = '--- SESSION INFORMATION ---';
    parts{end+1} = sprintf('Model: %s', reportData.metadata.modelName);
    parts{end+1} = sprintf('Generated: %s', reportData.metadata.generatedTime);
    parts{end+1} = sprintf('Time Range: [%.4g, %.4g]', ...
        reportData.metadata.timeRange(1), reportData.metadata.timeRange(2));
    parts{end+1} = sprintf('Total Steps: %d', reportData.metadata.numSteps);
    parts{end+1} = sprintf('Profile Time: %.4g seconds', reportData.metadata.profileTime);

    % Execution info if available
    if ~isempty(fieldnames(reportData.metadata.executionInfo))
        if isfield(reportData.metadata.executionInfo, 'StopEvent')
            parts{end+1} = sprintf('Stop Event: %s', ...
                reportData.metadata.executionInfo.StopEvent);
        end
    end

    % Files
    if ~isempty(reportData.metadata.statesFiles.xout)
        parts{end+1} = sprintf('States File: %s', reportData.metadata.statesFiles.xout);
    end
    if ~isempty(reportData.metadata.statesFiles.simlog)
        parts{end+1} = sprintf('Simlog File: %s', reportData.metadata.statesFiles.simlog);
    end
    parts{end+1} = '';

    % === STATISTICS ===
    parts{end+1} = '--- SIMULATION STATISTICS ---';
    parts{end+1} = utilFormatTable(reportData.statistics.tableContent, ...
        {'Property', 'Value'});
    parts{end+1} = '';

    % Join all parts
    text = strjoin(parts, '\n');
end
