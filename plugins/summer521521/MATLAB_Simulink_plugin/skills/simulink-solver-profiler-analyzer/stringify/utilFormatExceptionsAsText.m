% Copyright 2026 The MathWorks, Inc.
function text = utilFormatExceptionsAsText(reportData)
%UTILFORMATEXCEPTIONSASTEXT Format solver exception data from a profiler report as plain text
%
% Takes the structured reportData from utilExtractReportData and formats
% only the solver exceptions section as readable text.

    import solverprofiler.util.*

    parts = {};

    % === HEADER ===
    parts{end+1} = '==========================================================';
    parts{end+1} = 'SOLVER PROFILER REPORT';
    parts{end+1} = '==========================================================';
    parts{end+1} = '';

    % === SOLVER EXCEPTIONS ===
    parts{end+1} = '--- SOLVER EXCEPTIONS ---';
    parts{end+1} = sprintf('Total Failures: %d', reportData.advanced.failureInfo.totalFailures);
    parts{end+1} = sprintf('  - Tolerance: %d', reportData.advanced.failureInfo.toleranceFailures);
    parts{end+1} = sprintf('  - Newton Iteration: %d', reportData.advanced.failureInfo.newtonFailures);
    parts{end+1} = sprintf('  - Infinite State: %d', reportData.advanced.failureInfo.infiniteStateFailures);
    parts{end+1} = sprintf('  - Infinite Derivative: %d', reportData.advanced.failureInfo.infiniteDerivFailures);
    parts{end+1} = sprintf('  - DAE Min Step: %d', reportData.advanced.failureInfo.daeFailures);
    parts{end+1} = '';

    if ~isempty(reportData.tables.exceptions.content)
        parts{end+1} = utilFormatTable(reportData.tables.exceptions.content, ...
            reportData.tables.exceptions.columnNames);
    else
        parts{end+1} = '(No solver exception data)';
    end
    parts{end+1} = '';

    % Join all parts
    text = strjoin(parts, '\n');
end
