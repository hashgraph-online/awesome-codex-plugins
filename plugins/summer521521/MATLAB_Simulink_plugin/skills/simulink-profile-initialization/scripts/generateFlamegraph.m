function generateFlamegraph(matFile, outFile)
%generateFlamegraph Generate an interactive HTML flamegraph from Performance Tracer data.
%   generateFlamegraph(matFile) loads the specified .mat file and produces
%   an HTML flamegraph in the current directory.
%
%   generateFlamegraph(matFile, outFile) saves to the specified path.

    if nargin < 1
        matFile = 'perfTracer.mat';
    end

    [~, flamegraphJson, totalWall] = parsePerfTracerData(matFile);

    % Read HTML template
    skillDir = fileparts(mfilename('fullpath'));
    templateFile = fullfile(skillDir, '..', 'reference', 'flamegraph_template.html');
    html = fileread(templateFile);
    html = strrep(html, '{{FLAMEGRAPH_DATA}}', flamegraphJson);
    html = strrep(html, '{{TOTAL_TIME}}', sprintf('%.3f', totalWall));
    html = strrep(html, '{{DATE}}', char(datetime("now", 'Format', 'yyyy-MM-dd HH:mm:ss')));

    if nargin < 2
        outFile = fullfile(pwd, 'flamegraph_perfTracer.html');
    end

    fid = fopen(outFile, 'w', 'n', 'UTF-8');
    fwrite(fid, html, 'char');
    fclose(fid);
    fprintf('Flamegraph saved to: %s\n', outFile);
end
