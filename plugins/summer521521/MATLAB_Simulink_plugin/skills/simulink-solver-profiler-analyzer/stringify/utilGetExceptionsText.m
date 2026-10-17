% Copyright 2026 The MathWorks, Inc.
function text = utilGetExceptionsText(input)
%UTILGETEXCEPTIONSTEXT Get solver profiler exception data as formatted text
%
%   text = solverprofiler.util.utilGetExceptionsText(result) returns formatted text
%   from a profileModel result structure.
%
%   text = solverprofiler.util.utilGetExceptionsText(filepath) returns formatted text
%   from a saved session file.
%
% Example:
%   res = solverprofiler.profileModel('myModel');
%   text = solverprofiler.util.utilGetExceptionsText(res);
%   aiResponse = yourAIAnalysisFunction(text);

import solverprofiler.util.*

% Determine input type and load session data
if isobject(input) && isa(input, 'solverprofiler.internal.SolverProfilerSessionDataClass')
    % Direct session data object
    reportData = utilExtractReportData(input);
    reportData.metadata.sessionFile = '';
elseif isstruct(input) && isfield(input, 'file')
    % Result struct from profileModel
    sessionFile = input.file;
    data = load(sessionFile);
    sessionData = data.sessionData;
    reportData = utilExtractReportData(sessionData);
    reportData.metadata.sessionFile = sessionFile;
elseif ischar(input) || isstring(input)
    % File path
    if exist(char(input), 'file')
        sessionFile = char(input);
    else
        error('solverprofiler:util:utilGetExceptionsText:FileNotFound', ...
            'File not found: %s', input);
    end
    data = load(sessionFile);
    sessionData = data.sessionData;
    reportData = utilExtractReportData(sessionData);
    reportData.metadata.sessionFile = sessionFile;
else
    error('solverprofiler:util:utilGetExceptionsText:InvalidInput', ...
        'Input must be a result struct, session file path, or SolverProfilerSessionDataClass object');
end

% Limit to first 10 entries
if ~isempty(reportData.tables.exceptions.content)
    reportData.tables.exceptions.content = ...
        reportData.tables.exceptions.content(1:min(10,end), :);
end

% Format as text (solver exceptions only)
text = utilFormatExceptionsAsText(reportData);
end
