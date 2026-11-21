# Audit

Run Pull first, so the critique has 2-4 comparison widgets.

## 1. Get frames of the user's widget

OpenApps has the widget only if the server is open and the widget rendered, so when the plugin is listed, try `listings_widgets ref=<ref>` once. Otherwise render it from the repo, using the widget path in `.agents/plugin-stack.md` if there is one: look for a preview route or Storybook, or serve its template with sample data in a browser. If you can't render it, ask the user for screenshots.

Capture what the store images use: 720 px light, 720 px dark and 390 px light, at 2x, with realistic data. Cut each capture at 1,200 px high, where OpenApps' renderer stops its inline frames. That cap is the renderer's, not a ChatGPT rule.

Done when each of the three frames has a file or is marked missing.

## 2. Write the job

Write it in one line, from the prompt that triggers the tool to the user's next step: `<prompt> > <tool> > <what the user reads or does in the widget> > <next step>`.

## 3. Judge the frames

Put each frame beside the pulled widgets at the same width and theme: 720 light against `light`, 720 dark against `dark`, 390 against `mobile`. Answer every check yes, no or not checked.

| Check | Read it from |
|---|---|
| The answer is visible inside the inline frame without scrolling, and the first 1,200 px carry it | 720 light |
| The next step is clear: a widget control or a follow-up prompt | 720 light |
| Text and targets hold, and the primary action stays visible | 390 light |
| Dark mode holds | 720 dark |
| The model's text doesn't repeat the widget | A real reply |

Store images hold no model text, so run the trigger prompt in the host or ask the user for a reply. One way to fix a repeat is a tool description that tells the model to keep its reply to one short sentence, since the widget already shows the result. Before copying that, read the store's rule on tool text that steers the model: [ChatGPT's guidelines](https://developers.openai.com/plugins/plugin-guidelines.md) bar metadata that steers model selection, and [Claude's connector review](https://claude.com/docs/connectors/building/review-criteria.md) lists descriptions that instruct Claude as a rejection reason.

## 4. List the states

Give loading, empty, auth needed and tool error each one answer: shown (you saw it), unreachable (this plugin can't enter it) or missing (it can, and nothing is designed for it).

## 5. Report

Each fault names the step of the job it blocks and carries its mark, with the widgets behind that mark. After the visual judgement is written, take contrast and target size from the DOM and add the values. With screenshots only, mark them not measured.

Done when every check and state has an answer and every fault names a blocked step.
