% Copyright 2026 The MathWorks, Inc.
function mapping = utilResolveSimscapeStates(result)
%UTILRESOLVESIMSCAPESTATES Resolve Simscape state paths to Simulink block paths
%
%   mapping = solverprofiler.util.utilResolveSimscapeStates(result) returns a
%   struct array with fields 'statePath' and 'blockPath' for each Simscape
%   state found in result.SimscapeLoggingData.
%
%   If SimscapeLoggingData is empty or unavailable, returns an empty struct
%   array.
%
% Example:
%   res = solverprofiler.profileModel('myModel');
%   mapping = solverprofiler.util.utilResolveSimscapeStates(res);
%   for i = 1:numel(mapping)
%       fprintf('%s -> %s\n', mapping(i).statePath, mapping(i).blockPath);
%   end

    mapping = struct('statePath', {}, 'blockPath', {});

    % Get SimscapeLoggingData from result
    if ~isstruct(result) || ~isfield(result, 'SimscapeLoggingData')
        return
    end

    simlog = result.SimscapeLoggingData;
    if isempty(simlog)
        return
    end

    % Recursively traverse the simlog tree to find all leaf nodes (states)
    mapping = traverseNode(simlog, '', mapping);
end

function mapping = traverseNode(node, prefix, mapping)
    % Get child names from the simlog node
    try
        children = childNames(node);
    catch
        children = {};
    end

    for i = 1:numel(children)
        name = children{i};
        child = node.(name);

        if isempty(prefix)
            currentPath = name;
        else
            currentPath = [prefix '.' name];
        end

        % Check if this is a leaf node (a loggable state with getSource)
        if isobject(child) && ismethod(child, 'getSource')
            try
                blockPath = getfullname(getSource(child));
                entry = struct('statePath', currentPath, 'blockPath', blockPath);
                mapping(end + 1) = entry; %#ok<AGROW>
            catch
                % Resolution failed — record with empty blockPath
                entry = struct('statePath', currentPath, 'blockPath', '');
                mapping(end + 1) = entry; %#ok<AGROW>
            end
        else
            % Recurse into child node
            mapping = traverseNode(child, currentPath, mapping);
        end
    end
end
