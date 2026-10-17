% Copyright 2026 The MathWorks, Inc.
function text = utilGetStatisticsText(input)
%UTILGETSTATISTICSTEXT Get solver profiler session information and statistics as formatted text
%
%   text = solverprofiler.util.utilGetStatisticsText(result) returns formatted text
%   from a profileModel result structure.
%
%   text = solverprofiler.util.utilGetStatisticsText(filepath) returns formatted text
%   from a saved session file.
%
% Example:
%   res = solverprofiler.profileModel('myModel');
%   text = solverprofiler.util.utilGetStatisticsText(res);
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
        error('solverprofiler:util:utilGetStatisticsText:FileNotFound', ...
            'File not found: %s', input);
    end
    data = load(sessionFile);
    sessionData = data.sessionData;
    reportData = utilExtractReportData(sessionData);
    reportData.metadata.sessionFile = sessionFile;
else
    error('solverprofiler:util:utilGetStatisticsText:InvalidInput', ...
        'Input must be a result struct, session file path, or SolverProfilerSessionDataClass object');
end

% Format as text (statistics only)
text = utilFormatStatisticsAsText(reportData);
end
