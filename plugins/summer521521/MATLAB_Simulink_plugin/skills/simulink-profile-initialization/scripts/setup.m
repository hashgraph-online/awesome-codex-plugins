function setup()
%SETUP Add this folder to the MATLAB path.
%   setup() adds the folder containing this script to the MATLAB path,
%   making all skill functions available regardless of where the skill
%   is installed or which AI agent is used.

    thisDir = fileparts(mfilename('fullpath'));
    if ~contains(path, thisDir, 'IgnoreCase', ispc)
        addpath(thisDir);
        fprintf('Added to MATLAB path: %s\n', thisDir);
    else
        fprintf('Already on MATLAB path: %s\n', thisDir);
    end
end
