% Copyright 2026 The MathWorks, Inc.
function reportData = utilExtractReportData(sessionData)
%UTILEXTRACTREPORTDATA Extract all profiler data into a structured format

    import solverprofiler.util.*
    
    % Get the actual data
    SPData = sessionData.getActualDataFromSolverProfilerSessionData();
    
    % The data is in a .data field (lowercase!)
    if isstruct(SPData) && isfield(SPData, 'data')
        SPData = SPData.data;
    elseif isstruct(SPData) && isfield(SPData, 'Data')
        SPData = SPData.Data;
    end
    
    % Debug check
    if isempty(SPData)
        error('solverprofiler:utilExtractReportData:NoData', ...
            'Session data is empty');
    end
    
    % Initialize report data structure
    reportData = struct();
    
    % === Get SortedPD - this is the main data container ===
    sortedPD = getField(SPData, 'SortedPD');
    if isempty(sortedPD)
        % Maybe SPData IS the SortedPD?
        if isfield(SPData, 'Tout') || (isobject(SPData) && isprop(SPData, 'Tout'))
            sortedPD = SPData;
        else
            % Show what we have for debugging
            if isstruct(SPData)
                availFields = strjoin(fieldnames(SPData), ', ');
            elseif isobject(SPData)
                availFields = strjoin(properties(SPData), ', ');
            else
                availFields = class(SPData);
            end
            error('solverprofiler:utilExtractReportData:NoSortedPD', ...
                'Cannot find SortedPD in session data. Available fields: %s', ...
                availFields);
        end
    end
    
    % === METADATA ===
    reportData.metadata = extractMetadata(sessionData, SPData);
    
    % === STATISTICS ===
    reportData.statistics = extractStatistics(sortedPD);
    
    % === DIAGNOSTICS ===
    reportData.diagnostics = extractDiagnostics(SPData);
    
    % === TABLES ===
    % Setup time range
    tout = getField(sortedPD, 'Tout');
    if isempty(tout)
        timeRange = [];
    else
        timeRange = [tout(1)-32*eps, tout(end)+32*eps];
    end
    
    reportData.tables = struct();
    reportData.tables.zeroCrossings = extractZeroCrossingTable(sortedPD, timeRange);
    reportData.tables.exceptions = extractExceptionTable(sortedPD, timeRange);
    reportData.tables.resets = extractResetTable(sortedPD, timeRange);
    reportData.tables.jacobian = extractJacobianTable(sortedPD, timeRange);
    reportData.tables.inaccurateStates = extractInaccurateStateTable(sortedPD);
    reportData.tables.simscapeStiffness = extractSscStiffTable(sortedPD);
    
    % === ADDITIONAL DATA ===
    reportData.advanced = struct();
    reportData.advanced.blockStateStats = extractBlockStateStats(sortedPD);
    reportData.advanced.failureInfo = extractFailureInfo(sortedPD);
    reportData.advanced.zcInfo = extractZCInfo(sortedPD);
    reportData.advanced.resetInfo = extractResetInfo(sortedPD);
end

function value = getField(obj, fieldName)
    % Safely get a field from object or struct
    if isobject(obj)
        if isprop(obj, fieldName)
            value = obj.(fieldName);
        else
            value = [];
        end
    elseif isstruct(obj)
        if isfield(obj, fieldName)
            value = obj.(fieldName);
        else
            value = [];
        end
    else
        value = [];
    end
end

function metadata = extractMetadata(sessionData, SPData)
    metadata = struct();
    
    % Model info - try multiple sources
    metadata.modelName = '';
    if isobject(sessionData) && isprop(sessionData, 'Model')
        metadata.modelName = sessionData.Model;
    elseif isstruct(sessionData) && isfield(sessionData, 'Model')
        metadata.modelName = sessionData.Model;
    end
    
    if isempty(metadata.modelName)
        metadata.modelName = getField(SPData, 'Model');
    end
    
    if isempty(metadata.modelName)
        metadata.modelName = 'Unknown';
    end
    
    metadata.sessionFile = '';
    
    % Get SortedPD for other metadata
    sortedPD = getField(SPData, 'SortedPD');
    if isempty(sortedPD) && (isfield(SPData, 'Tout') || (isobject(SPData) && isprop(SPData, 'Tout')))
        sortedPD = SPData;  % SPData IS SortedPD
    end
    
    % Execution info
    metaData = getField(sortedPD, 'MetaData');
    if ~isempty(metaData) && isstruct(metaData) && isfield(metaData, 'ExecutionInfo')
        metadata.executionInfo = metaData.ExecutionInfo;
    else
        metadata.executionInfo = struct();
    end
    
    % States files
    if isobject(sessionData) && ismethod(sessionData, 'getStatesFileName')
        try
            metadata.statesFiles = sessionData.getStatesFileName();
        catch
            metadata.statesFiles = struct('xout', '', 'simlog', '');
        end
    else
        metadata.statesFiles = struct('xout', '', 'simlog', '');
    end
    
    % Time range
    tout = getField(sortedPD, 'Tout');
    if ~isempty(tout)
        metadata.timeRange = [tout(1), tout(end)];
        metadata.numSteps = length(tout) - 1;
    else
        metadata.timeRange = [0, 0];
        metadata.numSteps = 0;
    end
    
    % Profile time
    profileTime = getField(sortedPD, 'ProfileTime');
    if isempty(profileTime)
        profileTime = getField(SPData, 'ProfileTime');
    end
    metadata.profileTime = profileTime;
    if isempty(metadata.profileTime)
        metadata.profileTime = 0;
    end
    
    metadata.generatedTime = datestr(now, 'yyyy-mm-dd HH:MM:SS');
end

function stats = extractStatistics(sortedPD)
    stats = struct();
    
    % Get overview
    overview = getField(sortedPD, 'Overview');
    
    if ~isempty(overview)
        % Try to get simplified overview
        if isobject(overview) && ismethod(overview, 'getSimplifiedOverview')
            stats.overview = overview.getSimplifiedOverview();
        else
            stats.overview = struct();
        end
        
        % Try to get table content
        if isobject(overview) && ismethod(overview, 'getOverviewTableContent')
            stats.tableContent = overview.getOverviewTableContent();
        else
            stats.tableContent = {};
        end
    else
        stats.overview = struct();
        stats.tableContent = {};
    end
end

function diag = extractDiagnostics(SPData)
    diag = struct();
    
    % Get diagnostic messages
    diag.messages = getField(SPData, 'OverallDiag');
    if isempty(diag.messages)
        diag.messages = {};
    end
    
    % Get rules
    spRule = getField(SPData, 'SPRule');
    if ~isempty(spRule)
        diag.rules = getField(spRule, 'RuleSet');
    else
        diag.rules = [];
    end
end

function tableData = extractZeroCrossingTable(sortedPD, timeRange)
    tableData = struct();
    tableData.content = [];
    tableData.indices = [];
    tableData.columnNames = {'Count', 'Block'};
    
    if ~isempty(timeRange) && isobject(sortedPD) && ismethod(sortedPD, 'updateZeroCrossingTableContent')
        try
            [content, indices] = sortedPD.updateZeroCrossingTableContent(timeRange);
            tableData.content = content;
            tableData.indices = indices;
        catch
            % Method exists but failed
        end
    end
end

function tableData = extractExceptionTable(sortedPD, timeRange)
    tableData = struct();
    tableData.content = [];
    tableData.indices = [];
    tableData.columnNames = {'Type', 'Count', 'States Involved', ...
        'Time Span', 'Average', 'Max', 'Model State'};
    
    if ~isempty(timeRange) && isobject(sortedPD) && ismethod(sortedPD, 'updateExceptionTableContent')
        try
            [content, indices] = sortedPD.updateExceptionTableContent(timeRange, 1);
            tableData.content = content;
            tableData.indices = indices;
        catch
            % Method exists but failed
        end
    end
end

function tableData = extractResetTable(sortedPD, timeRange)
    tableData = struct();
    tableData.content = [];
    tableData.indices = [];
    tableData.columnNames = {'Block', 'ZC Reset', 'Discrete', ...
        'ZOH Signal', 'Initial', 'Block Reset', 'Internal', 'Time'};
    
    if ~isempty(timeRange) && isobject(sortedPD) && ismethod(sortedPD, 'getResetTableContent')
        try
            [content, indices] = sortedPD.getResetTableContent(timeRange);
            tableData.content = content;
            tableData.indices = indices;
        catch
            % Method exists but failed
        end
    end
end

function tableData = extractJacobianTable(sortedPD, timeRange)
    tableData = struct();
    tableData.content = [];
    tableData.indices = [];
    tableData.columnNames = {'Likelihood', 'Limiting States'};
    
    if ~isempty(timeRange) && isobject(sortedPD) && ismethod(sortedPD, 'updateJacobianTableContent')
        try
            [content, indices] = sortedPD.updateJacobianTableContent(timeRange);
            tableData.content = content;
            tableData.indices = indices;
        catch
            % Method exists but failed
        end
    end
end

function tableData = extractInaccurateStateTable(sortedPD)
    tableData = struct();
    tableData.content = [];
    tableData.indices = [];
    tableData.columnNames = {'xmin', 'xmax', 'abstol', 'State'};
    
    if isobject(sortedPD) && ismethod(sortedPD, 'getInaccurateStateTableContent')
        try
            [content, indices] = sortedPD.getInaccurateStateTableContent();
            tableData.content = content;
            tableData.indices = indices;
        catch
            % Method exists but failed
        end
    end
end

function tableData = extractSscStiffTable(sortedPD)
    tableData = struct();
    tableData.content = [];
    tableData.columnNames = {'Stiff Times', 'Stiffness', 'Stiff States'};
    
    if isobject(sortedPD) && ismethod(sortedPD, 'getSscStiffTableContent')
        try
            tableData.content = sortedPD.getSscStiffTableContent();
        catch
            % Method exists but failed
        end
    end
end

function blockStats = extractBlockStateStats(sortedPD)
    blockStats = struct();
    blockStats.numBlocksWithStates = 0;
    blockStats.numStates = 0;
    
    bss = getField(sortedPD, 'BlockStateStats');
    if ~isempty(bss) && isobject(bss)
        try
            if ismethod(bss, 'getNumBlocksWithState')
                blockStats.numBlocksWithStates = bss.getNumBlocksWithState();
            end
            if ismethod(bss, 'getNumberOfStates')
                blockStats.numStates = bss.getNumberOfStates();
            end
        catch
            % Methods exist but failed
        end
    end
end

function failInfo = extractFailureInfo(sortedPD)
    failInfo = struct();
    failInfo.totalFailures = 0;
    failInfo.toleranceFailures = 0;
    failInfo.newtonFailures = 0;
    failInfo.infiniteStateFailures = 0;
    failInfo.infiniteDerivFailures = 0;
    failInfo.daeFailures = 0;
    
    fi = getField(sortedPD, 'FailureInfo');
    if ~isempty(fi) && isobject(fi) && ismethod(fi, 'getTotalFailureNum')
        try
            failInfo.totalFailures = fi.getTotalFailureNum(0);
            failInfo.toleranceFailures = fi.getTotalFailureNum(1);
            failInfo.newtonFailures = fi.getTotalFailureNum(2);
            failInfo.infiniteStateFailures = fi.getTotalFailureNum(3);
            failInfo.infiniteDerivFailures = fi.getTotalFailureNum(4);
            failInfo.daeFailures = fi.getTotalFailureNum(5);
        catch
            % Methods exist but failed
        end
    end
end

function zcInfo = extractZCInfo(sortedPD)
    zcInfo = struct();
    zcInfo.numSources = 0;
    zcInfo.numTriggeredSources = 0;
    zcInfo.totalZeroCrossings = 0;
    
    zc = getField(sortedPD, 'ZcInfo');
    if ~isempty(zc) && isobject(zc)
        try
            if ismethod(zc, 'numSrcs')
                zcInfo.numSources = zc.numSrcs();
            end
            if ismethod(zc, 'numTriggerdSrcs')
                zcInfo.numTriggeredSources = zc.numTriggerdSrcs();
            end
            if ismethod(zc, 'totalZcNum')
                zcInfo.totalZeroCrossings = zc.totalZcNum();
            end
        catch
            % Methods exist but failed
        end
    end
end

function resetInfo = extractResetInfo(sortedPD)
    resetInfo = struct();
    resetInfo.totalResets = 0;
    resetInfo.zcResets = 0;
    resetInfo.discreteResets = 0;
    resetInfo.zohResets = 0;
    resetInfo.initialResets = 0;
    resetInfo.blockResets = 0;
    resetInfo.internalResets = 0;
    
    if isobject(sortedPD) && ismethod(sortedPD, 'getTotalResetNum')
        try
            resetInfo.totalResets = sortedPD.getTotalResetNum(0);
            resetInfo.zcResets = sortedPD.getTotalResetNum(1);
            resetInfo.discreteResets = sortedPD.getTotalResetNum(2);
            resetInfo.zohResets = sortedPD.getTotalResetNum(3);
            resetInfo.initialResets = sortedPD.getTotalResetNum(4);
            resetInfo.blockResets = sortedPD.getTotalResetNum(5);
            resetInfo.internalResets = sortedPD.getTotalResetNum(6);
        catch
            % Methods exist but failed
        end
    end
end