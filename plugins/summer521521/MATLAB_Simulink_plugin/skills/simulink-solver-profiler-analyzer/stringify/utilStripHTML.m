function cleanText = utilStripHTML(text)
%UTILSTRIPHTML Remove HTML tags and clean whitespace
if isempty(text)
    cleanText = '';
    return;
end

% Convert to char if needed
text = char(text);

% Remove HTML tags
cleanText = regexprep(text, '<[^>]*>', '');

% Replace char(160) non-breaking spaces with regular spaces
cleanText = strrep(cleanText, char(160), ' ');

% Trim whitespace
cleanText = strtrim(cleanText);
end