% Copyright 2026 The MathWorks, Inc.
function cleanData = utilCleanTableData(tableData)
%UTILCLEANTABLEDATA Clean table data by removing HTML and formatting values

import solverprofiler.util.*

cleanData = cell(size(tableData));

for i = 1:numel(tableData)
    if ischar(tableData{i}) || isstring(tableData{i})
        cleanData{i} = utilStripHTML(char(tableData{i}));
    elseif isnumeric(tableData{i})
        cleanData{i} = num2str(tableData{i});
    else
        cleanData{i} = '';
    end
end
end