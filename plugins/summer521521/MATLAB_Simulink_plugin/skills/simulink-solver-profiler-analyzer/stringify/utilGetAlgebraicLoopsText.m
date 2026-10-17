% Copyright 2026 The MathWorks, Inc.
function text = utilGetAlgebraicLoopsText(modelName)
%UTILGETALGEBRAICLOOPSTEXT Detect algebraic loops and return results as formatted text
%
%   text = solverprofiler.util.utilGetAlgebraicLoopsText(modelName) returns
%   formatted text listing all blocks involved in algebraic loops.
%
% Example:
%   text = solverprofiler.util.utilGetAlgebraicLoopsText('myModel');
%   disp(text)

    [algebraicLoopInfo, h] = Simulink.BlockDiagram.getAlgebraicLoops(modelName);

    if ~isempty(h)
        close(h);
        blockPaths = getfullname(algebraicLoopInfo.BlockHandles);
        if ischar(blockPaths)
            blockPaths = {blockPaths};
        end

        lines = cell(numel(blockPaths) + 3, 1);
        lines{1} = sprintf('=== Algebraic Loops (%s) ===', modelName);
        lines{2} = sprintf('Found %d block(s) inside algebraic loops:', numel(blockPaths));
        lines{3} = '';
        for i = 1:numel(blockPaths)
            lines{3 + i} = sprintf('  %d. %s', i, blockPaths{i});
        end
        text = strjoin(lines, newline);
    else
        text = sprintf('=== Algebraic Loops (%s) ===\nNo algebraic loops found.', modelName);
    end
end
