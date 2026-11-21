# Finding format

Every confirmed finding uses these fields in this order. Subagents return them; the parent reports them unchanged except for severity adjustments and merged class labels.

```
### [S-n] [short title naming the defect and the asset]

Severity: [critical | high | medium | low]
Class: [defect class; list several if merged]
Location: [file:line, the line where the defect is introduced]

Exploit path:
1. Attacker ([starting position]) sends/supplies [input] via [entry point, file:line].
2. [hop, file:line]
3. Reaches [sink, file:line] and causes [effect].

Evidence: [failing test | reproduction | trace]
[Test: full content and run command, plus what it asserts and the failure output.
 Reproduction: exact input and the observed or traced result.
 Trace: each hop with file:line and the reason no control on the path stops it.]

Why existing controls do not stop it: [name the middleware, validator, or type you checked and why it does not apply]

Fix direction: [one or two sentences naming the specific change at a specific location]
```

## Field rules

**Title.** Name the defect and what it exposes. "SQL injection in report filter exposes all tenants' invoices" is useful. "Injection issue" is too vague to triage.

**Location.** The diff line that introduces the defect. If the defect sits in old code that the diff makes reachable, give both: the old sink and the diff line that opens the path.

**Exploit path.** Start from an attacker position someone could realistically hold. Each hop cites code. If a hop depends on configuration, say which setting and where it is set.

**Evidence.** One of the three kinds is required. A finding whose evidence is "this looks unsafe" goes to needs verification.

**Why existing controls do not stop it.** This field forces the reviewer to look for the control before claiming it is missing. It is the most common reason findings get demoted.

**Fix direction.** Specific to this code. "Bind `status` as a query parameter in `reports/query.py:142`" is acceptable. "Sanitize inputs" is not.

## Needs-verification items

```
- [file:line] [what you suspect, one sentence]. Missing: [the hop or evidence you could not establish]. To settle: [the exact check, test, or question for the user].
```

## Example (illustrative, fictional code)

```
### S-1 Path traversal in export download reads arbitrary files

Severity: high
Class: path traversal
Location: api/exports.py:57

Exploit path:
1. Authenticated user calls GET /exports/download?name=../../etc/app.env (api/routes.py:112).
2. download() joins EXPORT_DIR and name with os.path.join and no normalization check (api/exports.py:57).
3. send_file() returns the joined path's contents (api/exports.py:61), exposing the app's environment file with the database password.

Evidence: failing test
  tests/scratch/test_export_traversal.py
  def test_rejects_parent_segments(client, user_token):
      r = client.get("/exports/download", params={"name": "../../etc/app.env"},
                     headers={"Authorization": f"Bearer {user_token}"})
      assert r.status_code == 400
  Run: pytest tests/scratch/test_export_traversal.py
  Result: fails, status 200 with file contents.

Why existing controls do not stop it: the auth middleware (api/middleware.py:30) checks only that the user is logged in; no validator runs on `name`.

Fix direction: resolve the joined path and reject it unless it is inside EXPORT_DIR (api/exports.py:57), or look exports up by ID instead of filename.
```
