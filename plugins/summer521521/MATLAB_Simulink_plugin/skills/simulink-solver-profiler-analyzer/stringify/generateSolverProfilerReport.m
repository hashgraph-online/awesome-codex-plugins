% Copyright 2026 The MathWorks, Inc.
function generateSolverProfilerReport(input, findings, outFile)
%generateSolverProfilerReport Generate an HTML Solver Profiler report.
%
%   generateSolverProfilerReport(result, findings) generates a report from
%   a profileModel result struct. 'findings' is a string containing the
%   LLM-authored findings and recommendations as HTML (using <ol class="rec-list">
%   with <li class="priority-high|medium|low"> items for recommendations).
%
%   generateSolverProfilerReport(filepath, findings) loads from a session file.
%
%   generateSolverProfilerReport(..., findings, outFile) saves to the specified path.
%
%   Example:
%     result = solverprofiler.profileModel('MyModel');
%     findings = '<ol class="rec-list"><li class="priority-high"><strong>Fix solver resets</strong>Add First Order Hold blocks.</li></ol>';
%     generateSolverProfilerReport(result, findings);

    import solverprofiler.util.*

    % --- Load session data ---
    if isobject(input) && isa(input, 'solverprofiler.internal.SolverProfilerSessionDataClass')
        % Direct session data object
        reportData = utilExtractReportData(input);
        reportData.metadata.sessionFile = '';
    elseif isstruct(input) && isfield(input, 'file')
        sessionFile = input.file;
        data = load(sessionFile);
        sessionData = data.sessionData;
        reportData = utilExtractReportData(sessionData);
        reportData.metadata.sessionFile = sessionFile;
    elseif ischar(input) || isstring(input)
        sessionFile = char(input);
        data = load(sessionFile);
        sessionData = data.sessionData;
        reportData = utilExtractReportData(sessionData);
        reportData.metadata.sessionFile = sessionFile;
    else
        error('generateSolverProfilerReport:InvalidInput', ...
            'Input must be a profileModel result struct, session file path, or SolverProfilerSessionDataClass object.');
    end

    if nargin < 2 || isempty(findings)
        findings = '';
    end

    % --- Read template ---
    skillDir = fileparts(mfilename('fullpath'));
    templateFile = fullfile(skillDir, '..', 'reference', 'template.html');
    html = fileread(templateFile);

    % --- Extract key statistics ---
    stats = parseStatisticsTable(reportData.statistics.tableContent);
    modelName = char(reportData.metadata.modelName);

    % --- Replace scalar tokens ---
    html = strrep(html, '{{MODEL_NAME}}', htmlEsc(modelName));
    html = strrep(html, '{{DATE}}', char(datetime("now", 'Format', 'yyyy-MM-dd')));
    html = strrep(html, '{{SOLVER}}', htmlEsc(stats.solver));
    html = strrep(html, '{{TOTAL_STEPS}}', formatNum(stats.totalSteps));
    html = strrep(html, '{{RUN_TIME}}', sprintf('%.1f s', reportData.metadata.profileTime));

    % Jacobian
    html = strrep(html, '{{JACOBIAN_UPDATES}}', formatNum(stats.jacobianUpdates));
    if stats.totalSteps > 0 && stats.jacobianUpdates / stats.totalSteps > 0.01
        html = strrep(html, '{{JACOBIAN_COLOR}}', 'var(--red)');
    else
        html = strrep(html, '{{JACOBIAN_COLOR}}', 'var(--green)');
    end

    % Exceptions
    html = strrep(html, '{{SOLVER_EXCEPTIONS}}', formatNum(stats.solverExceptions));
    if stats.totalSteps > 0 && stats.solverExceptions / stats.totalSteps > 0.01
        html = strrep(html, '{{EXCEPTIONS_COLOR}}', 'var(--red)');
    else
        html = strrep(html, '{{EXCEPTIONS_COLOR}}', 'var(--green)');
    end

    % Resets
    html = strrep(html, '{{SOLVER_RESETS}}', formatNum(stats.solverResets));
    if stats.solverResets > 100
        html = strrep(html, '{{RESETS_COLOR}}', 'var(--red)');
    elseif stats.solverResets > 10
        html = strrep(html, '{{RESETS_COLOR}}', 'var(--yellow)');
    else
        html = strrep(html, '{{RESETS_COLOR}}', 'var(--green)');
    end

    % Zero crossings
    html = strrep(html, '{{ZERO_CROSSINGS}}', formatNum(stats.zeroCrossings));
    if stats.zeroCrossings > 1000
        html = strrep(html, '{{ZC_COLOR}}', 'var(--red)');
    elseif stats.zeroCrossings > 100
        html = strrep(html, '{{ZC_COLOR}}', 'var(--yellow)');
    else
        html = strrep(html, '{{ZC_COLOR}}', 'var(--green)');
    end

    % --- Session info rows ---
    sessionHtml = buildSessionInfoRows(reportData);
    html = strrep(html, '{{SESSION_INFO_ROWS}}', sessionHtml);

    % --- Exceptions section ---
    html = strrep(html, '{{EXCEPTIONS_SECTION}}', buildExceptionsSection(reportData));

    % --- Resets section ---
    html = strrep(html, '{{RESETS_SECTION}}', buildResetsSection(reportData));

    % --- Zero crossings section ---
    html = strrep(html, '{{ZC_SECTION}}', buildZCSection(reportData));

    % --- Algebraic loops section ---
    html = strrep(html, '{{ALGEBRAIC_LOOPS_SECTION}}', '');

    % --- Warnings section ---
    html = strrep(html, '{{WARNINGS_SECTION}}', buildWarningsSection(reportData));

    % --- Recommendations section ---
    if strlength(string(findings)) > 0
        html = strrep(html, '{{RECOMMENDATIONS_SECTION}}', findings);
    else
        html = strrep(html, '{{RECOMMENDATIONS_SECTION}}', ...
            '<div class="card"><p style="color:var(--muted);">No findings provided. Pass a findings string to generateSolverProfilerReport to populate this section.</p></div>');
    end

    % --- Save ---
    if nargin < 3 || isempty(outFile)
        outFile = fullfile(pwd, sprintf('SolverProfilerReport_%s.html', modelName));
    end
    fid = fopen(outFile, 'w', 'n', 'UTF-8');
    fwrite(fid, html, 'char');
    fclose(fid);
    fprintf('Report saved to: %s\n', outFile);
end

%% --- Parse statistics table content into a struct ---
function s = parseStatisticsTable(tableContent)
    s.solver = 'unknown';
    s.totalSteps = 0;
    s.jacobianUpdates = 0;
    s.solverExceptions = 0;
    s.solverResets = 0;
    s.zeroCrossings = 0;

    if isempty(tableContent)
        return;
    end

    for i = 1:size(tableContent, 1)
        key = lower(strtrim(stripHtmlTags(char(tableContent{i, 1}))));
        val = strtrim(stripHtmlTags(char(tableContent{i, 2})));

        if contains(key, 'solver type') || contains(key, 'solver name')
            s.solver = val;
        elseif contains(key, 'total step') && ~contains(key, 'jacobian') && ~contains(key, 'reset')
            s.totalSteps = parseNumericVal(val);
        elseif contains(key, 'jacobian')
            s.jacobianUpdates = parseNumericVal(val);
        elseif contains(key, 'exception') || contains(key, 'failure')
            s.solverExceptions = s.solverExceptions + parseNumericVal(val);
        elseif contains(key, 'reset') && ~contains(key, 'block') && ~contains(key, 'internal')
            s.solverResets = parseNumericVal(val);
        elseif contains(key, 'zero crossing') || contains(key, 'zero-crossing')
            s.zeroCrossings = parseNumericVal(val);
        end
    end
end

function n = parseNumericVal(str)
    str = regexprep(str, '[,\s]', '');
    n = str2double(str);
    if isnan(n)
        n = 0;
    end
end

function s = stripHtmlTags(str)
    s = regexprep(str, '<[^>]*>', '');
end

%% --- Build session info rows ---
function s = buildSessionInfoRows(rd)
    s = '';
    s = addRow(s, 'Model', htmlEsc(char(rd.metadata.modelName)));
    s = addRow(s, 'Time Range', sprintf('[%.4g, %.4g]', rd.metadata.timeRange(1), rd.metadata.timeRange(2)));
    s = addRow(s, 'Total Steps', formatNum(rd.metadata.numSteps));
    s = addRow(s, 'Profile Time', sprintf('%.4g s', rd.metadata.profileTime));
    s = addRow(s, 'Blocks with States', formatNum(rd.advanced.blockStateStats.numBlocksWithStates));
    s = addRow(s, 'Total States', formatNum(rd.advanced.blockStateStats.numStates));

    if ~isempty(rd.metadata.sessionFile)
        s = addRow(s, 'Session File', sprintf('<code>%s</code>', htmlEsc(rd.metadata.sessionFile)));
    end

    % Statistics table rows
    if ~isempty(rd.statistics.tableContent)
        for i = 1:size(rd.statistics.tableContent, 1)
            key = strtrim(stripHtmlTags(char(rd.statistics.tableContent{i, 1})));
            val = strtrim(stripHtmlTags(char(rd.statistics.tableContent{i, 2})));
            s = addRow(s, key, val);
        end
    end
end

function s = addRow(s, label, value)
    s = [s, sprintf('<tr><td>%s</td><td>%s</td></tr>\n', label, value)];
end

%% --- Build exceptions section ---
function s = buildExceptionsSection(rd)
    fi = rd.advanced.failureInfo;
    if fi.totalFailures == 0
        s = '';
        return;
    end

    badge = severityBadge(fi.totalFailures, 100, 10);
    s = sprintf('<h2>%s Solver Exceptions</h2>\n<div class="card">\n', badge);

    % Summary
    s = [s, '<table>' newline];
    s = addRow(s, 'Total Failures', formatNum(fi.totalFailures));
    s = addRow(s, 'Error Control (tolerance)', formatNum(fi.toleranceFailures));
    s = addRow(s, 'Newton Iteration', formatNum(fi.newtonFailures));
    s = addRow(s, 'Infinite State', formatNum(fi.infiniteStateFailures));
    s = addRow(s, 'Infinite Derivative', formatNum(fi.infiniteDerivFailures));
    s = addRow(s, 'DAE Newton Iteration', formatNum(fi.daeFailures));
    s = [s, '</table>' newline];

    % Detail table
    if ~isempty(rd.tables.exceptions.content)
        s = [s, buildDetailTable(rd.tables.exceptions.content, rd.tables.exceptions.columnNames)];
    end

    s = [s, '</div>' newline];
end

%% --- Build resets section ---
function s = buildResetsSection(rd)
    ri = rd.advanced.resetInfo;
    if ri.totalResets == 0
        s = '';
        return;
    end

    badge = severityBadge(ri.totalResets, 100, 10);
    s = sprintf('<h2>%s Solver Resets</h2>\n<div class="card">\n', badge);

    s = [s, '<table>' newline];
    s = addRow(s, 'Total Resets', formatNum(ri.totalResets));
    s = addRow(s, 'Zero Crossing', formatNum(ri.zcResets));
    s = addRow(s, 'Discrete Signal', formatNum(ri.discreteResets));
    s = addRow(s, 'ZOH Signal', formatNum(ri.zohResets));
    s = addRow(s, 'Initial', formatNum(ri.initialResets));
    s = addRow(s, 'Block Reset', formatNum(ri.blockResets));
    s = addRow(s, 'Internal', formatNum(ri.internalResets));
    s = [s, '</table>' newline];

    if ~isempty(rd.tables.resets.content)
        s = [s, buildDetailTable(rd.tables.resets.content, rd.tables.resets.columnNames)];
    end

    s = [s, '</div>' newline];
end

%% --- Build zero crossings section ---
function s = buildZCSection(rd)
    zi = rd.advanced.zcInfo;
    if zi.totalZeroCrossings == 0
        s = '';
        return;
    end

    badge = severityBadge(zi.totalZeroCrossings, 1000, 100);
    s = sprintf('<h2>%s Zero Crossings</h2>\n<div class="card">\n', badge);

    s = [s, '<table>' newline];
    s = addRow(s, 'Total Sources', formatNum(zi.numSources));
    s = addRow(s, 'Triggered Sources', formatNum(zi.numTriggeredSources));
    s = addRow(s, 'Total Events', formatNum(zi.totalZeroCrossings));
    s = [s, '</table>' newline];

    if ~isempty(rd.tables.zeroCrossings.content)
        s = [s, buildDetailTable(rd.tables.zeroCrossings.content, rd.tables.zeroCrossings.columnNames)];
    end

    s = [s, '</div>' newline];
end

%% --- Build warnings section from diagnostics ---
function s = buildWarningsSection(rd)
    msgs = rd.diagnostics.messages;
    if isempty(msgs)
        s = '';
        return;
    end

    s = ['<h2><span class="badge badge-yellow">Warning</span> Diagnostics</h2>' newline '<div class="card">' newline];
    for i = 1:numel(msgs)
        txt = char(msgs{i});
        if ~isempty(strtrim(txt))
            s = [s, '<p>' txt '</p>' newline]; %#ok<AGROW>
        end
    end
    s = [s, '</div>' newline];
end

%% --- Build an HTML table from cell array data ---
function s = buildDetailTable(content, colNames)
    s = ['<table style="margin-top:0.75rem;">' newline '<thead><tr>'];
    for j = 1:numel(colNames)
        s = [s, '<th>' htmlEsc(colNames{j}) '</th>']; %#ok<AGROW>
    end
    s = [s, '</tr></thead>' newline '<tbody>' newline];

    for i = 1:size(content, 1)
        s = [s, '<tr>']; %#ok<AGROW>
        for j = 1:min(numel(colNames), size(content, 2))
            val = content{i, j};
            if ischar(val) || isstring(val)
                cellStr = char(val);
            elseif isnumeric(val)
                cellStr = num2str(val);
            else
                cellStr = '';
            end
            % Preserve block path hyperlinks if already in HTML
            if contains(cellStr, '<a ')
                s = [s, '<td>' cellStr '</td>']; %#ok<AGROW>
            else
                s = [s, '<td>' htmlEsc(cellStr) '</td>']; %#ok<AGROW>
            end
        end
        s = [s, '</tr>' newline]; %#ok<AGROW>
    end
    s = [s, '</tbody></table>' newline];
end

%% --- Helpers ---
function b = severityBadge(count, highThresh, medThresh)
    if count > highThresh
        b = '<span class="badge badge-red">Critical</span>';
    elseif count > medThresh
        b = '<span class="badge badge-yellow">Warning</span>';
    else
        b = '<span class="badge badge-green">Low</span>';
    end
end

function s = formatNum(n)
    % Format number with comma separators
    str = sprintf('%d', n);
    len = length(str);
    if len <= 3
        s = str;
        return;
    end
    parts = {};
    while len > 3
        parts{end+1} = str(len-2:len); %#ok<AGROW>
        str = str(1:len-3);
        len = length(str);
    end
    parts{end+1} = str;
    s = strjoin(flip(parts), ',');
end

function t = htmlEsc(str)
    t = strrep(str, '&', '&amp;');
    t = strrep(t, '<', '&lt;');
    t = strrep(t, '>', '&gt;');
    t = strrep(t, '"', '&quot;');
end
