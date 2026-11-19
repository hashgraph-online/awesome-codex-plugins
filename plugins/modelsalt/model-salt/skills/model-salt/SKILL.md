---
name: model-salt
description: Use before any creative or open-ended request (a picture, an SVG, a story, a poem, an email, a design, a name, a tagline, a plan) so the result is varied and still exactly what was asked. Calls the model_salt tool, then follows what it returns. Skip it for tasks with one right answer.
---
Call the `model_salt` tool before you do the request, in the form its own description asks for:

- **It takes `counts`** (the hosted server at modelsalt.com, used by the Claude Code plugin): first write in your reply the decisions and the numbered options for each that its instructions name, option 1 the usual choice. Then call `model_salt` with only how many options each decision has, for example `{"counts": [5, 5, 5, 5, 5]}`. Use exactly the option numbers it returns: write each decision with its drawn option in one short line, then make the result so it shows every drawn option.
- **It takes `request`** (the local server run with `npx`): call it with the user's request word for word in `request` and your model name in `model`. If it returns an exploring step with an `id` (it does when this machine has no Claude Code or Codex to run that step on), do that step without showing it to the user, then call `model_salt` again with `model`, that `id` and your whole reply to the step in `explored`. Then do the request exactly as the last returned text says.

If no `model_salt` tool is available, carry on with the request without it.
