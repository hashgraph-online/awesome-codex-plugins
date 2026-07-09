function setBlockDimensions(block, width, height)
% SETBLOCKDIMENSIONS  Resize a Simulink/Simscape block without moving it.
%
%   setBlockDimensions(block, width, height)
%
%   Inputs:
%     block  - block path (char/string) or block handle (numeric)
%     width  - desired block width  (Simulink canvas coordinates)
%     height - desired block height (Simulink canvas coordinates)
%
%   The top-left corner (x, y) is preserved; only the size changes.

    if isnumeric(block)
        blockPath = getfullname(block);
    else
        blockPath = char(block);
    end

    pos    = get_param(blockPath, 'Position');   % [left, top, right, bottom]
    newPos = [pos(1), pos(2), pos(1) + width, pos(2) + height];

    set_param(blockPath, 'Position', newPos);
end
