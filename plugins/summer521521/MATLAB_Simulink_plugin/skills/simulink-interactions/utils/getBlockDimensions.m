function [width, height] = getBlockDimensions(block)
% GETBLOCKDIMENSIONS  Return the width and height of a Simulink/Simscape block.
%
%   [width, height] = getBlockDimensions(block)
%
%   Input:
%     block  - block path (char/string) or block handle (numeric)
%
%   Outputs:
%     width  - block width  (Simulink canvas coordinates)
%     height - block height (Simulink canvas coordinates)

    if isnumeric(block)
        blockPath = getfullname(block);
    else
        blockPath = char(block);
    end

    pos    = get_param(blockPath, 'Position');   % [left, top, right, bottom]
    width  = pos(3) - pos(1);
    height = pos(4) - pos(2);
end
