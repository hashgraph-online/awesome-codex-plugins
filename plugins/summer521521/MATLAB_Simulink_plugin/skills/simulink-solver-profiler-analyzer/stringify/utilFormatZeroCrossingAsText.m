% Copyright 2026 The MathWorks, Inc.
function text = utilFormatZeroCrossingAsText(reportData)
%UTILFORMATZERCROSSINGASTEXT Format zero-crossing data from a profiler report as plain text
%
% Takes the structured reportData from utilExtractReportData and formats
% only the zero-crossing section as readable text.

    import solverprofiler.util.*

    parts = {};

    % === HEADER ===
    parts{end+1} = '==========================================================';
    parts{end+1} = 'SOLVER PROFILER REPORT';
    parts{end+1} = '==========================================================';
    parts{end+1} = '';

    % === ZERO CROSSINGS ===
    parts{end+1} = '--- ZERO CROSSINGS ---';
    parts{end+1} = sprintf('Total Sources: %d', reportData.advanced.zcInfo.numSources);
    parts{end+1} = sprintf('Triggered Sources: %d', reportData.advanced.zcInfo.numTriggeredSources);
    parts{end+1} = sprintf('Total Events: %d', reportData.advanced.zcInfo.totalZeroCrossings);
    parts{end+1} = '';

    if ~isempty(reportData.tables.zeroCrossings.content)
        parts{end+1} = utilFormatTable(reportData.tables.zeroCrossings.content, ...
            reportData.tables.zeroCrossings.columnNames);
    else
        parts{end+1} = '(No zero-crossing data)';
    end
    parts{end+1} = '';

    % Join all parts
    text = strjoin(parts, '\n');
end
