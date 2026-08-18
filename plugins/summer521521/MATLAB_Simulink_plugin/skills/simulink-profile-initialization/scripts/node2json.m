function s = node2json(node)
%node2json Recursively convert a flamegraph node struct to a JSON string.
%
%   s = node2json(node) converts a struct with fields 'name', 'start',
%   'duration', and 'children' (cell array) into a JSON string.

    s = sprintf('{"name":"%s","start":%.6f,"duration":%.6f,"children":[', ...
        jsonEscape(node.name), node.start, node.duration);
    for k = 1:numel(node.children)
        if k > 1
            s = [s, ',']; %#ok<AGROW>
        end
        s = [s, node2json(node.children{k})]; %#ok<AGROW>
    end
    s = [s, ']}'];
end
