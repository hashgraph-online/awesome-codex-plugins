---
name: supportpages
description: Create or retry illustrated help articles with WTFM (by SupportPages.io) using its MCP connection and article writer. Use for WTFM or SupportPages.io article requests, including generating an unpublished draft for review.
---

<!-- Managed by SupportPages: article coordination v1 -->

# WTFM articles

Use the SupportPages.io MCP connection for the current project.

For inventory questions such as "what support articles do we have?", call
`supportpages_list_articles` directly, without status or initialization first.
When signed out or in local mode it reads the project's current local article
files. Report those titles and paths without asking the user to sign in. An empty
local list means no local articles were found, not that the hosted help centre is
empty. Do not infer the inventory from Git status. Use `source: "hosted"` only
when the user explicitly asks what is on SupportPages.io.

For article creation, check
`supportpages_status`, finish initialization if required, and call
`supportpages_prepare_article` before writing. Follow the returned readiness or
capacity instructions. Show the prepared editor link; a preview is not a finished
draft.

When the prepared run has `prefer_background: true`, **delegate the writing task
to a background subagent**. This skill explicitly requests delegation for that
article. Use the SupportPages.io writer and the returned Codex launch instructions,
including the complete task brief, model settings and self-contained entrypoint.
Pass the complete task brief directly in the subagent tool's task/message argument
on launches and retries. Do not copy it into a temporary JSON file, create a
handoff script, or print it with a shell command. The existing entrypoint already
loads the saved run; no parent-side file edit is needed to launch the writer.
If no custom-agent selector exists, use a named SupportPages.io subagent with the
supplied writer instructions. The writer runs the entrypoint before generating
anything, uses the command wrapper, and runs the finish command after validation.

**Prioritize completion and approvals over quiet operation.** After launch,
record the actual execution mode and host task identity with
`supportpages_update_run`. Show the editor link and say "launched" unless actual
writer startup is confirmed. Keep the main turn active and supervise the writer
using the host's agent wait/message facilities. Use bounded waits and concise
progress updates; do not end the turn merely because launch succeeded.

The writer may send milestone updates and must surface blockers immediately.
When an operation needs permission and host policy permits it, the writer should
request approval directly through the host's native approval mechanism, with the
exact command and reason. A sandbox restriction is not an explicit user denial.
Do not suppress approval prompts or route them only to an idle parent. Continue
after approval is granted. An explicit denial or a policy forbidding approval
requests stops that action; never bypass it or enable YOLO.

If a background writer cannot surface approvals, confirm it has stopped and
continue the same article in the foreground using MCP recovery instructions and
the normal approval mechanism. Foreground execution retains the same permissions.
If the host cannot supervise a delegated task, use foreground execution. Keep
the MCP session alive; do not launch a separate agent CLI.

Inspect the writer's final result and saved run. A host "Completed" notification
does not establish success. For a stopped writer that failed or is
`permission_blocked` before generation finished, record `event: "failed"` and
`stopped: true` with `supportpages_update_run`, then show the specific cause,
recovery and editor link. Do not mark a writer failed while awaiting approval.
If generation succeeded but delivery is pending or failed, recover with
`supportpages_complete_article` without regenerating or marking the writer failed.

The main agent owns MCP calls. After successful writing, call
`supportpages_complete_article` to confirm delivery, report the final editor link
and follow its completion instructions. Leave the article unpublished until the
user affirmatively asks to publish that draft.

**Local folders.** When `supportpages_status` or `supportpages_init` reports
`local`, the folder has no help centre and needs no sign-in: articles are saved
as Markdown with their screenshots. There is no capacity check, preview or editor
link. Show the saved markdown path returned by `supportpages_complete_article` as
the deliverable and never ask whether to publish automatically. Mention once
that running `wtfm publish` in the terminal hosts the saved articles.

If the user explicitly asks to host or publish saved local articles, call
`supportpages_publish`. Follow its browser approval and help-centre selection
steps, then pass the selected article slugs. It uploads drafts and connects the
folder for future articles. Do not accept credentials in chat or approve sign-in
for the user. Making those drafts publicly visible is a separate action using
`supportpages_publish_article` when authorized.

**Hosted analysis and videos.** Use `supportpages_find_article_gaps`,
`supportpages_suggest_sections`, `supportpages_recommend_articles` or
`supportpages_create_video_walkthrough` for the requested action. These tools
check the prerequisites and open required browser setup pages. When signed out,
first explain that an account/device sign-in is needed; sign in or create an
account through the opened approval page. Do not begin with a repository invitation
or send the user to the app homepage. Show the comparison code, and show the link
as a fallback if `browser_opened` is false. Never approve browser consent.

After the user completes a step, call `supportpages_setup_hosted` with the
returned `next_arguments`. Ask which help centre to use when `project_required`
is returned (or use `supportpages_create_project` if the user wants a new one),
then pass its `project_id`. The next required device-consent or repository setup
page opens automatically. Preserve the original request and `resume_arguments`
through these steps; do not start local analysis, recording or unrelated jobs.
Once setup is available, retry `resume_tool` with `resume_arguments`. Walkthroughs
require a completed hosted article: use `supportpages_list_articles` with
`source: "hosted"` to select it. Do not restore deleted files or upload a local
article without the user's explicit instruction. Finished videos remain private
until explicitly shared.

Honor an explicit request to return immediately, explaining that approvals and
completion may need another user turn on hosts that do not wake the parent.
Retain the run ID and host task identity; reconcile the run on resumption.

Honor an explicit foreground request. If delegation cannot run, distinguish a
missing host tool, an explicit session restriction, or the actual launch error;
do not infer that background execution is disabled merely because the user did
not separately request a subagent. Explain the specific limitation and use the
same prepared brief in the foreground. Stop any launched writer before switching
modes. Do not override host restrictions or launch a separate agent CLI.

For retries, follow the MCP recovery instructions and use
`supportpages_retry_article` after stopping the old writer. If generation already
finished and delivery failed, recover delivery instead of regenerating.
