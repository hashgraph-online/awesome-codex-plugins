function t = jsonEscape(str)
%jsonEscape Escape special characters for JSON string embedding.
%
%   t = jsonEscape(str) escapes backslashes, double quotes, newlines,
%   and carriage returns in str.

    t = strrep(str, '\', '\\');
    t = strrep(t, '"', '\"');
    t = strrep(t, newline, ' ');
    t = strrep(t, char(13), '');
end
