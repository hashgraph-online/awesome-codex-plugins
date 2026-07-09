function generateProfilerReport(results, findings, outFile)
%generateProfilerReport Generate an HTML report from Simulink Profiler results.
%
%   generateProfilerReport(results, findings) generates an HTML report in
%   the current directory. 'results' is the struct returned by
%   parseSimulinkProfilerData. 'findings' is a string or char array of
%   findings and recommendations (Markdown-formatted text is accepted;
%   paragraphs are wrapped in <p> tags, lines starting with "- " become
%   list items).
%
%   generateProfilerReport(results, findings, outFile) saves to the
%   specified path.
%
%   Example:
%     results = parseSimulinkProfilerData(profilerData);
%     findings = "## Key Findings\n- Scope blocks dominate init time\n\n## Recommendations\n- Disable scopes for batch runs";
%     generateProfilerReport(results, findings);

    arguments
        results (1,1) struct
        findings (1,1) string = ""
        outFile (1,1) string = ""
    end

    N_BLOCKS = 20;
    N_EXEC = 20;

    % --- Read template ---
    skillDir = fileparts(mfilename('fullpath'));
    templateFile = fullfile(skillDir, '..', 'reference', 'profiler_report_template.html');
    html = fileread(templateFile);

    % --- Model info ---
    html = strrep(html, '{{MODEL_NAME}}', char(results.modelName));
    html = strrep(html, '{{TOTAL_TIME}}', sprintf('%.2f', results.totalSimTime));
    html = strrep(html, '{{DATE}}', char(datetime("now", 'Format', 'yyyy-MM-dd HH:mm:ss')));

    % --- Summary items ---
    phases = results.phases;
    dominantPhase = char(phases.Phase(1));
    dominantPct = phases.PctOfTotal(1);
    nBlocks = height(results.blockProfiles);
    nExec = height(results.execTree);

    summaryHtml = sprintf([ ...
        '<div class="summary-item"><div class="value" style="color:var(--red);">%.2f s</div><div class="label">Total Time</div></div>\n' ...
        '<div class="summary-item"><div class="value">%s</div><div class="label">Dominant Phase (%.0f%%)</div></div>\n' ...
        '<div class="summary-item"><div class="value">%d</div><div class="label">Profiled Blocks</div></div>\n' ...
        '<div class="summary-item"><div class="value">%d</div><div class="label">Exec Nodes</div></div>\n'], ...
        results.totalSimTime, dominantPhase, dominantPct, nBlocks, nExec);
    html = strrep(html, '{{SUMMARY_ITEMS}}', summaryHtml);

    % --- Phase rows ---
    phaseHtml = '';
    colors = {'#d73a49','#e36209','#b08800','#28a745','#0366d6','#6f42c1','#586069','#959da5'};
    for i = 1:height(phases)
        pct = phases.PctOfTotal(i);
        ci = mod(i-1, numel(colors)) + 1;
        barHtml = sprintf('<div class="bar-container"><div class="bar-fill" style="width:%.1f%%;background:%s;"></div></div>', pct, colors{ci});
        phaseHtml = [phaseHtml, sprintf( ...
            '<tr><td><code>%s</code></td><td class="num">%.3f</td><td class="num">%.3f</td><td class="num">%d</td><td class="num">%.1f%%</td><td>%s</td></tr>\n', ...
            htmlEscape(char(phases.Phase(i))), phases.TotalTime_s(i), phases.SelfTime_s(i), ...
            phases.Calls(i), pct, barHtml)]; %#ok<AGROW>
    end
    html = strrep(html, '{{PHASE_ROWS}}', phaseHtml);

    % --- Block hotspot rows (sorted by SelfTime descending) ---
    bp = sortrows(results.blockProfiles, 'SelfTime_s', 'descend');
    N = min(N_BLOCKS, height(bp));
    blockHtml = '';
    for i = 1:N
        p = bp.Path{i};
        pathStr = strjoin(string(p), ' &gt; ');
        perCall = 0;
        if bp.Calls(i) > 0
            perCall = bp.SelfTime_s(i) / bp.Calls(i) * 1000; % ms
        end
        blockHtml = [blockHtml, sprintf( ...
            '<tr><td class="num">%d</td><td><code>%s</code></td><td class="num">%.3f</td><td class="num">%.3f</td><td class="num">%d</td><td class="num">%.3f</td></tr>\n', ...
            i, pathStr, bp.TotalTime_s(i), bp.SelfTime_s(i), bp.Calls(i), perCall)]; %#ok<AGROW>
    end
    html = strrep(html, '{{BLOCK_ROWS}}', blockHtml);

    % --- Exec tree rows (sorted by SelfTime descending) ---
    et = sortrows(results.execTree, 'SelfTime_s', 'descend');
    N = min(N_EXEC, height(et));
    execHtml = '';
    for i = 1:N
        obj = strjoin(string(et.ObjectPath{i}), ' &gt; ');
        loc = char(string(et.Location(i)));
        perCall = 0;
        if et.Calls(i) > 0
            perCall = et.SelfTime_s(i) / et.Calls(i) * 1000; % ms
        end
        execHtml = [execHtml, sprintf( ...
            '<tr><td class="num">%d</td><td><code>%s</code></td><td><code>%s</code></td><td class="num">%.3f</td><td class="num">%.3f</td><td class="num">%d</td><td class="num">%.3f</td></tr>\n', ...
            i, htmlEscape(loc), obj, et.TotalTime_s(i), et.SelfTime_s(i), et.Calls(i), perCall)]; %#ok<AGROW>
    end
    html = strrep(html, '{{EXEC_ROWS}}', execHtml);

    % --- Findings & Recommendations ---
    if strlength(findings) > 0
        findingsHtml = ['<div class="card">' newline markdownToHtml(findings) newline '</div>'];
    else
        findingsHtml = '<div class="card"><p style="color:var(--muted);">No findings provided. Pass a findings string to generateProfilerReport to populate this section.</p></div>';
    end
    html = strrep(html, '{{FINDINGS_SECTION}}', findingsHtml);

    % --- Save ---
    if outFile == ""
        outFile = fullfile(pwd, sprintf('ProfilerReport_%s.html', char(results.modelName)));
    end
    fid = fopen(outFile, 'w', 'n', 'UTF-8');
    fwrite(fid, html, 'char');
    fclose(fid);
    fprintf('Report saved to: %s\n', outFile);
end

%% --- Markdown-like text to simple HTML ---
function s = markdownToHtml(txt)
    lines = splitlines(char(txt));
    s = '';
    inList = false;
    for i = 1:numel(lines)
        line = strtrim(lines{i});
        if isempty(line)
            if inList
                s = [s, '</ul>' newline]; %#ok<AGROW>
                inList = false;
            end
            continue;
        end
        % Headings
        if startsWith(line, '### ')
            if inList, s = [s, '</ul>' newline]; inList = false; end %#ok<AGROW>
            s = [s, '<h3>' htmlEscape(line(5:end)) '</h3>' newline]; %#ok<AGROW>
        elseif startsWith(line, '## ')
            if inList, s = [s, '</ul>' newline]; inList = false; end %#ok<AGROW>
            s = [s, '<h3 style="margin-top:1rem;">' htmlEscape(line(4:end)) '</h3>' newline]; %#ok<AGROW>
        % List items
        elseif startsWith(line, '- ') || startsWith(line, '* ')
            if ~inList
                s = [s, '<ul style="margin:0.5rem 0 0.5rem 1.5rem;">' newline]; %#ok<AGROW>
                inList = true;
            end
            s = [s, '<li>' htmlEscape(line(3:end)) '</li>' newline]; %#ok<AGROW>
        % Numbered items
        elseif ~isempty(regexp(line, '^\d+[\.\)] ', 'once'))
            if ~inList
                s = [s, '<ul style="margin:0.5rem 0 0.5rem 1.5rem;">' newline]; %#ok<AGROW>
                inList = true;
            end
            content = regexprep(line, '^\d+[\.\)] ', '');
            s = [s, '<li>' htmlEscape(content) '</li>' newline]; %#ok<AGROW>
        % Bold standalone lines
        elseif startsWith(line, '**') && endsWith(line, '**')
            if inList, s = [s, '</ul>' newline]; inList = false; end %#ok<AGROW>
            s = [s, '<p><strong>' htmlEscape(line(3:end-2)) '</strong></p>' newline]; %#ok<AGROW>
        % Regular paragraphs
        else
            if inList, s = [s, '</ul>' newline]; inList = false; end %#ok<AGROW>
            s = [s, '<p>' htmlEscape(line) '</p>' newline]; %#ok<AGROW>
        end
    end
    if inList
        s = [s, '</ul>' newline];
    end
end

%% --- HTML escape ---
function t = htmlEscape(str)
    t = strrep(str, '&', '&amp;');
    t = strrep(t, '<', '&lt;');
    t = strrep(t, '>', '&gt;');
    t = strrep(t, '"', '&quot;');
end
