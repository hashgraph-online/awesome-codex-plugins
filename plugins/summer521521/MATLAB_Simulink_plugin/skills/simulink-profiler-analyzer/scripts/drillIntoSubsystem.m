function drillIntoSubsystem(execTree, subsystemName, threshold)
%drillIntoSubsystem  Filter exec tree to show nodes inside a subsystem.
%
%   drillIntoSubsystem(execTree, subsystemName) displays exec nodes whose
%   ObjectPath contains subsystemName and whose SelfTime_s exceeds 0.001 s.
%
%   drillIntoSubsystem(execTree, subsystemName, threshold) uses a custom
%   self-time threshold in seconds.
%
%   execTree is the results.execTree table returned by
%   parseSimulinkProfilerData.

    arguments
        execTree table
        subsystemName (1,1) string
        threshold (1,1) double {mustBeNonnegative} = 0.001
    end

    et = execTree;
    found = false;

    fprintf('\n--- Drill-down: "%s" (selfTime > %.4f s) ---\n\n', subsystemName, threshold);
    for i = 1:height(et)
        obj = strjoin(string(et.ObjectPath{i}), ' > ');
        loc = string(et.Location(i));
        if contains(obj, subsystemName) && et.SelfTime_s(i) > threshold
            perCall = 0;
            if et.Calls(i) > 0
                perCall = et.SelfTime_s(i) / et.Calls(i);
            end
            fprintf('  %8.4f s (self %8.4f, %.4f s/call) calls=%5d  %s [%s]\n', ...
                et.TotalTime_s(i), et.SelfTime_s(i), perCall, et.Calls(i), loc, obj);
            found = true;
        end
    end

    if ~found
        fprintf('  No exec nodes matched "%s" with selfTime > %.4f s.\n', subsystemName, threshold);
    end
    fprintf('\n');
end
