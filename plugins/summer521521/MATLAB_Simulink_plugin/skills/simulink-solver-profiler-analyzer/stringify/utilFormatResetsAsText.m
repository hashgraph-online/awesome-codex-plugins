% Copyright 2026 The MathWorks, Inc.
function text = utilFormatResetsAsText(reportData)
%UTILFORMATRESETSASTEXT Format solver reset data from a profiler report as plain text
%
% Takes the structured reportData from utilExtractReportData and formats
% only the solver resets section as readable text.

    import solverprofiler.util.*

    parts = {};

    % === HEADER ===
    parts{end+1} = '==========================================================';
    parts{end+1} = 'SOLVER PROFILER REPORT';
    parts{end+1} = '==========================================================';
    parts{end+1} = '';

    % === SOLVER RESETS ===
    parts{end+1} = '--- SOLVER RESETS ---';
    parts{end+1} = sprintf('Total Resets: %d', reportData.advanced.resetInfo.totalResets);
    parts{end+1} = sprintf('  - ZC Reset: %d', reportData.advanced.resetInfo.zcResets);
    parts{end+1} = sprintf('  - Discrete: %d', reportData.advanced.resetInfo.discreteResets);
    parts{end+1} = sprintf('  - ZOH Signal: %d', reportData.advanced.resetInfo.zohResets);
    parts{end+1} = sprintf('  - Initial: %d', reportData.advanced.resetInfo.initialResets);
    parts{end+1} = sprintf('  - Block Reset: %d', reportData.advanced.resetInfo.blockResets);
    parts{end+1} = sprintf('  - Internal: %d', reportData.advanced.resetInfo.internalResets);
    parts{end+1} = '';

    if ~isempty(reportData.tables.resets.content)
        parts{end+1} = utilFormatTable(reportData.tables.resets.content, ...
            reportData.tables.resets.columnNames);
    else
        parts{end+1} = '(No solver reset data)';
    end
    parts{end+1} = '';

    % Join all parts
    text = strjoin(parts, '\n');
end
