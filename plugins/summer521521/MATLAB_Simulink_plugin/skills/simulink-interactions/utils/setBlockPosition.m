function setBlockPosition(block, x, y)
% SETBLOCKPOSITION  Move a Simulink block to (x, y) preserving its size.
%   setBlockPosition(block, x, y)  where block is a path string or handle.
    pos = get_param(block, 'Position');
    w = pos(3) - pos(1);
    h = pos(4) - pos(2);
    set_param(block, 'Position', [x, y, x+w, y+h]);
end
