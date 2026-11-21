# Visual mode

The visual page lets the user step through the change. It covers the same content as the chat explanation, which it complements.

## Content

- Start with the problem and the result in two sentences.
- Show the flow as steps the user moves through. Each step shows the data at that point, such as a request, a row, or a message, what happens to it, and why.
- Let the user switch scenarios: the normal case, and each important edge case or error with what the user or operator sees.
- Explain each concept in a short note beside the step that uses it.
- Use the names a person sees or operates. Leave out internal files, functions, and variables.
- Take the cases from real data, tests, or logs. Replace personal data, customer names, and secrets with realistic invented values, and mark them as invented.

## Build

- In Claude Code, publish one page with the `Artifact` tool. It stays private until the user shares it.
- In Codex, or when that tool is missing, write one HTML file in the system temp directory and open it in the browser.
- Keep the page self-contained: inline CSS and JavaScript, and no network calls.
- Write every value into the page. The page never runs project code or reads project data.
- Before you give the link or path, try every control and every scenario.
