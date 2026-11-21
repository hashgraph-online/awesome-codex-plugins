# Target Project — One Project per Path in the Request

Plugin runtime asset. Loaded by `plan`, `document`, and `review` during context
resolution. It implements behaviors 49–52 and Failure Behavior 2 of
`command-surface-v2.spec` and the `project` argument of
`call-root-resolution.spec`.

## Terms

- **Session root** — the project the MCP server serves to a call without
  `project`.
- **Target project** — the nearest directory above a path in the request that
  holds `.archcore/`. The session root is the target project of a request that
  names no path.
- **`project` argument** — the absolute path of a target project root, passed
  to an Archcore MCP tool. The value is the directory that holds `.archcore/`,
  never `.archcore/` itself.

## Resolution

1. Resolve one target project for each path the request names.
2. WHEN a path is relative, resolve it against the session root.
3. WHEN the request names no path, use the session root as the only target project.
4. IF a path has no ancestor that holds `.archcore/`, THEN record the path as a target project without `.archcore/`.

## Calls

1. WHEN a read or write concerns a target project other than the session root, pass that root as `project`.
2. WHEN a call concerns the session root, omit `project`.
3. Keep both documents of one `add_relation` or `remove_relation` call in one target project.
4. IF a relation would join two target projects, THEN report the pair and create no relation.
5. WHEN a write concerns a global document, use the row's `source_root` as the target project.
6. WHEN a response carries a `source` other than `"local"`, name that source in the report. A change there reaches every project that declares the source.
7. Absent any global row and any `source` field, proceed as usual.

## Old CLI

An archcore CLI older than 0.15.0 ignores `project` and serves the session root.

1. Before the first write to a target project other than the session root, call `list_documents` with that root as `project`.
2. Do not make the call of step 1 before `init_project`; read the `init_project` response instead.
3. WHEN a call carries `project`, read the `project` field of the response.
4. IF a successful response to a call with `project` has no `project` field, THEN stop before the next write.
5. Report that the call reached the session root, and name `archcore update` as the fix.
6. IF an error response names `project` or `init_project`, THEN treat the CLI as 0.15.0 or newer and follow the error.

## Projects without `.archcore/`

1. WHEN the session root or a target project holds no `.archcore/`, name that root in the report.
2. Name the project roots the session recap listed, when it listed any.
3. Ask one question: which project to use, or whether to initialize the named root.
4. Do not call `init_project` before the user answers.
5. IF the host cannot deliver the question, for example in a non-interactive run, THEN name the roots, write nothing, and stop.
6. WHEN the user chooses to initialize a root other than the session root, call `init_project` with that root as `project`.

## Grounding and report

1. WHEN the request names more than one target project, run grounding in each target project.
2. Attribute each found document to its target project.
3. WHEN the request names more than one target project, list each produced or reviewed document beside its project root in the report.
4. WHEN all documents belong to the session root, report them as before, without a project column.
