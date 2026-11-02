---
name: model-salt
description: Use before any creative or open-ended request (a picture, an SVG, a story, a poem, an email, a design, a name, a tagline, a plan) so the result is varied and still exactly what was asked. Calls the model_salt tool with the request, then follows what it returns. Skip it for tasks with one right answer.
---
Call the `model_salt` tool once, with the user's request word for word in `request` and your model name in `model`. Then do the request exactly as the returned text says.

If no `model_salt` tool is available, carry on with the request without it.
