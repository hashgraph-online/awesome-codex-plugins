function [x, y] = getBlockPosition(block)
% GETBLOCKPOSITION  Return the top-left corner (x, y) of a Simulink block.
%   [x, y] = getBlockPosition(block)  where block is a path string or handle.
    pos = get_param(block, 'Position');
    x = pos(1);
    y = pos(2);
end
