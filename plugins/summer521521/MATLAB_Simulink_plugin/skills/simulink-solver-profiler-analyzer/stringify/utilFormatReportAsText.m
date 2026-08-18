% Copyright 2026 The MathWorks, Inc.
function text = utilFormatReportAsText(reportData)
%UTILFORMATREPORTASTEXT Format extracted report data as plain text
%
% Takes the structured reportData from utilExtractReportData and formats
% it as readable text suitable for AI analysis or human review

    import solverprofiler.util.*
    
    parts = {};
    
    % === HEADER ===
    parts{end+1} = '==========================================================';
    parts{end+1} = 'SOLVER PROFILER REPORT';
    parts{end+1} = '==========================================================';
    parts{end+1} = '';
    
    % === METADATA ===
    parts{end+1} = '--- SESSION INFORMATION ---';
    parts{end+1} = sprintf('Model: %s', reportData.metadata.modelName);
    parts{end+1} = sprintf('Generated: %s', reportData.metadata.generatedTime);
    parts{end+1} = sprintf('Time Range: [%.4g, %.4g]', ...
        reportData.metadata.timeRange(1), reportData.metadata.timeRange(2));
    parts{end+1} = sprintf('Total Steps: %d', reportData.metadata.numSteps);
    parts{end+1} = sprintf('Profile Time: %.4g seconds', reportData.metadata.profileTime);
    
    % Execution info if available
    if ~isempty(fieldnames(reportData.metadata.executionInfo))
        if isfield(reportData.metadata.executionInfo, 'StopEvent')
            parts{end+1} = sprintf('Stop Event: %s', ...
                reportData.metadata.executionInfo.StopEvent);
        end
    end
    
    % Files
    if ~isempty(reportData.metadata.statesFiles.xout)
        parts{end+1} = sprintf('States File: %s', reportData.metadata.statesFiles.xout);
    end
    if ~isempty(reportData.metadata.statesFiles.simlog)
        parts{end+1} = sprintf('Simlog File: %s', reportData.metadata.statesFiles.simlog);
    end
    parts{end+1} = '';
    
    % === STATISTICS ===
    parts{end+1} = '--- SIMULATION STATISTICS ---';
    parts{end+1} = utilFormatTable(reportData.statistics.tableContent, ...
        {'Property', 'Value'});
    parts{end+1} = '';
    
    % === DIAGNOSTICS ===
    if ~isempty(reportData.diagnostics.messages)
        parts{end+1} = '--- DIAGNOSTICS & RECOMMENDATIONS ---';
        for i = 1:length(reportData.diagnostics.messages)
            diagText = utilStripHTML(reportData.diagnostics.messages{i});
            if ~isempty(diagText)
                parts{end+1} = diagText;
            end
        end
        parts{end+1} = '';
    end
    
    % === TABLES ===
    
    % Zero Crossings
    if ~isempty(reportData.tables.zeroCrossings.content)
        parts{end+1} = '--- ZERO CROSSINGS ---';
        parts{end+1} = sprintf('Total Sources: %d', reportData.advanced.zcInfo.numSources);
        parts{end+1} = sprintf('Triggered Sources: %d', reportData.advanced.zcInfo.numTriggeredSources);
        parts{end+1} = sprintf('Total Events: %d', reportData.advanced.zcInfo.totalZeroCrossings);
        parts{end+1} = '';
        parts{end+1} = utilFormatTable(reportData.tables.zeroCrossings.content, ...
            reportData.tables.zeroCrossings.columnNames);
        parts{end+1} = '';
    end
    
    % Solver Exceptions
    if ~isempty(reportData.tables.exceptions.content)
        parts{end+1} = '--- SOLVER EXCEPTIONS ---';
        parts{end+1} = sprintf('Total Failures: %d', reportData.advanced.failureInfo.totalFailures);
        parts{end+1} = sprintf('  - Tolerance: %d', reportData.advanced.failureInfo.toleranceFailures);
        parts{end+1} = sprintf('  - Newton Iteration: %d', reportData.advanced.failureInfo.newtonFailures);
        parts{end+1} = sprintf('  - Infinite State: %d', reportData.advanced.failureInfo.infiniteStateFailures);
        parts{end+1} = sprintf('  - Infinite Derivative: %d', reportData.advanced.failureInfo.infiniteDerivFailures);
        parts{end+1} = sprintf('  - DAE Min Step: %d', reportData.advanced.failureInfo.daeFailures);
        parts{end+1} = '';
        parts{end+1} = utilFormatTable(reportData.tables.exceptions.content, ...
            reportData.tables.exceptions.columnNames);
        parts{end+1} = '';
    end
    
    % Solver Resets
    if ~isempty(reportData.tables.resets.content)
        parts{end+1} = '--- SOLVER RESETS ---';
        parts{end+1} = sprintf('Total Resets: %d', reportData.advanced.resetInfo.totalResets);
        parts{end+1} = sprintf('  - ZC Reset: %d', reportData.advanced.resetInfo.zcResets);
        parts{end+1} = sprintf('  - Discrete: %d', reportData.advanced.resetInfo.discreteResets);
        parts{end+1} = sprintf('  - ZOH Signal: %d', reportData.advanced.resetInfo.zohResets);
        parts{end+1} = sprintf('  - Initial: %d', reportData.advanced.resetInfo.initialResets);
        parts{end+1} = sprintf('  - Block Reset: %d', reportData.advanced.resetInfo.blockResets);
        parts{end+1} = sprintf('  - Internal: %d', reportData.advanced.resetInfo.internalResets);
        parts{end+1} = '';
        parts{end+1} = utilFormatTable(reportData.tables.resets.content, ...
            reportData.tables.resets.columnNames);
        parts{end+1} = '';
    end
    
    % Jacobian Analysis
    if ~isempty(reportData.tables.jacobian.content)
        parts{end+1} = '--- JACOBIAN ANALYSIS ---';
        parts{end+1} = utilFormatTable(reportData.tables.jacobian.content, ...
            reportData.tables.jacobian.columnNames);
        parts{end+1} = '';
    end
    
    % Inaccurate States
    if ~isempty(reportData.tables.inaccurateStates.content)
        parts{end+1} = '--- STATES BELOW ABSOLUTE TOLERANCE ---';
        parts{end+1} = utilFormatTable(reportData.tables.inaccurateStates.content, ...
            reportData.tables.inaccurateStates.columnNames);
        parts{end+1} = '';
    end
    
    % Simscape Stiffness
    if ~isempty(reportData.tables.simscapeStiffness.content)
        parts{end+1} = '--- SIMSCAPE STIFFNESS ANALYSIS ---';
        parts{end+1} = utilFormatTable(reportData.tables.simscapeStiffness.content, ...
            reportData.tables.simscapeStiffness.columnNames);
        parts{end+1} = '';
    end
    
    % === SUMMARY ===
    parts{end+1} = '--- SUMMARY ---';
    parts{end+1} = sprintf('Blocks with States: %d', ...
        reportData.advanced.blockStateStats.numBlocksWithStates);
    parts{end+1} = sprintf('Total States: %d', ...
        reportData.advanced.blockStateStats.numStates);
    parts{end+1} = '';
    
    % Join all parts
    text = strjoin(parts, '\n');
end