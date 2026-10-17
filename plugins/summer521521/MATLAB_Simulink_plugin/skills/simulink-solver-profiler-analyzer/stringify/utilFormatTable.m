% Copyright 2026 The MathWorks, Inc.
function tableText = utilFormatTable(tableData, columnNames)
%UTILFORMATTABLE Format a cell array table as aligned text

import solverprofiler.util.*

if isempty(tableData)
    tableText = '(No data)';
    return;
end

% Strip HTML and clean data
cleanData = utilCleanTableData(tableData);

% Calculate column widths
numCols = length(columnNames);
numRows = size(cleanData, 1);
colWidths = zeros(1, numCols);

% Width from headers
for j = 1:numCols
    colWidths(j) = length(columnNames{j});
end

% Width from data
for i = 1:numRows
    for j = 1:min(numCols, size(cleanData, 2))
        if ~isempty(cleanData{i,j})
            colWidths(j) = max(colWidths(j), length(cleanData{i,j}));
        end
    end
end

% Build header
lines = {};
headerLine = '';
for j = 1:numCols
    headerLine = [headerLine, sprintf('%-*s  ', colWidths(j), columnNames{j})];
end
lines{end+1} = strtrim(headerLine);
lines{end+1} = repmat('-', 1, length(lines{1}));

% Build rows
for i = 1:numRows
    rowLine = '';
    for j = 1:min(numCols, size(cleanData, 2))
        cellData = cleanData{i,j};
        if isempty(cellData)
            cellData = '';
        end
        rowLine = [rowLine, sprintf('%-*s  ', colWidths(j), cellData)];
    end
    lines{end+1} = strtrim(rowLine);
end

tableText = strjoin(lines, '\n');
end