function checkModelRefRebuild(diaryFile)
%checkModelRefRebuild Check ModelRefRebuild setting from a compile diary.
%   checkModelRefRebuild(diaryFile) reads the diary file (default:
%   'modelCompileDiary.txt') and reports the ModelRefRebuild value.
%
%   Expected good value: 'IfOutOfDate'
%   Flags 'IfOutOfDateOrStructuralChange' or 'Force' as inefficient.

    if nargin < 1
        diaryFile = 'modelCompileDiary.txt';
    end

    txt = fileread(diaryFile);
    lines = splitlines(txt);

    validValues = {'Force', 'IfOutOfDateOrStructuralChange', 'IfOutOfDate', 'AssumeUpToDate'};

    found = false;
    for i = 1:numel(lines)
        if contains(lines{i}, 'ModelRefRebuild')
            % The value is on one of the next 2 lines (there may be an empty line)
            val = '(unknown)';
            for j = 1:2
                if i + j <= numel(lines)
                    candidate = strtrim(lines{i+j});
                    candidate = strrep(candidate, '''', '');
                    if ismember(candidate, validValues)
                        val = candidate;
                        break;
                    end
                end
            end
            found = true;
            break;
        end
    end

    if ~found
        fprintf('WARNING: ModelRefRebuild not found in %s\n', diaryFile);
        return;
    end

    fprintf('\n=== MODEL REFERENCE REBUILD SETTING ===\n');
    fprintf('ModelRefRebuild = ''%s''\n\n', val);

    switch val
        case 'IfOutOfDate'
            fprintf('OK: This is the recommended setting ("If changes in known dependencies detected").\n');
        case 'AssumeUpToDate'
            fprintf('INFO: ''AssumeUpToDate'' skips all rebuild checks. Fast, but risks stale targets.\n');
            fprintf('RECOMMENDATION: Use only when you are certain no dependencies have changed.\n');
        case {'Force', 'IfOutOfDateOrStructuralChange', '(unknown)'}
            fprintf('WARNING: ''%s'' is inefficient and may cause unnecessary rebuilds.\n', val);
            fprintf('RECOMMENDATION: Change to ''IfOutOfDate'' ("If changes in known dependencies detected").\n');
            fprintf('  UI:   Model Settings > Model Referencing > Rebuild > "If changes in known dependencies detected"\n');
            fprintf('  Code: set_param(mdl, ''UpdateModelReferenceTargets'', ''IfOutOfDate'')\n');
    end
end
