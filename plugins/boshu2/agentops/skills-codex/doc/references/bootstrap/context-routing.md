# Explicit external context routes

The caller selects CDLC storage in an existing home config or an explicitly
selected file. Bootstrap creates neither a project config nor a bundle, staging
directory, evidence directory or maintenance anchor by default. Existing project
configuration remains readable. This reference describes the caller's separate
read-only `ao config context` operation; it does not add a Bootstrap setup step.

## Configuration and identity

`context` has no defaults and never consumes `paths.learnings_dir`. Every key
below is a string. Existing precedence applies: invocation overrides,
`AGENTOPS_CONTEXT_<UPPERCASE_KEY>`, project `.agents/ao/config.yaml`, home
`~/.agents/ao/config.yaml`. `AGENTOPS_CONFIG` / `--config` selects **only** that
file, excluding ambient home and project files. Missing explicit files and
malformed/unreadable route configuration fail closed. No command writes config.

```yaml
context:
  source_id: /srv/fixture/native/.beads
  project_id: fixture-native-project-id
  owner_scope: fixture-personal
  bundle_id: fixture-bundle-id
  bundle_root: /srv/fixture/knowledge
  evidence_root: /srv/fixture/evidence
  staging_root: /srv/fixture/staging
  access_policy_ref: /srv/fixture/policy.json
  owner_policy_ref: /srv/fixture/owner-policy.md
  task_policy_ref: /srv/fixture/task-policy.md
  model_policy_ref: /srv/fixture/model-policy.md
  destination_policy_ref: /srv/fixture/destination-policy.md
  maintenance_work_ref: fixture-maintenance-anchor
```

These are synthetic locators, not installation defaults. `source_id` names the
canonical `beads_dir` returned by the selected native `bd context --json`;
`project_id` is its native project identity. `owner_scope` is independently
supplied by the caller, never inferred from the repository basename. Clones,
worktrees, personal, employer and customer contexts do not merge implicitly.
All roots and policy files must already exist. Policy roots name canonical
absolute paths; an alias in the policy cannot silently retarget permission.

The independently selected access-policy JSON has these required fields:

```json
{
  "schema_version": 1,
  "source_id": "/srv/fixture/native/.beads",
  "project_id": "fixture-native-project-id",
  "owner_scope": "fixture-personal",
  "task_ref": "fixture-task",
  "model_ref": "fixture-provider/model",
  "destination_ref": "fixture-private-destination",
  "bundle_id": "fixture-bundle-id",
  "bundle_root": "/srv/fixture/knowledge",
  "evidence_root": "/srv/fixture/evidence",
  "staging_root": "/srv/fixture/staging",
  "owner_policy_ref": "/srv/fixture/owner-policy.md",
  "task_policy_ref": "/srv/fixture/task-policy.md",
  "model_policy_ref": "/srv/fixture/model-policy.md",
  "destination_policy_ref": "/srv/fixture/destination-policy.md",
  "maintenance_work_ref": "fixture-maintenance-anchor"
}
```

Unknown, duplicate, missing or incompatible policy fields are errors. The
selected policy and supplied purpose are checked before private anchor comments
are read. The individual policy references must resolve to existing regular
files; this command selects and checks their locators, not their prose or native
permission enforcement. It always reports `access_enforcement: not_attested`.
T39 owns measured native enforcement; this route result grants no new access,
model transmission, disclosure or Git ingestion permission.

Both evidence and staging must be external to the bundle, the explicitly named
consumer checkout, each other, ordinary/bare/linked Git repositories and active
Git storage bindings. Filesystem identities and symlink resolution prevent
aliases from bypassing these boundaries. As with the shared evidence helper,
ancestry cannot discover an unmarked directory referenced as external storage
by an unrelated repository. Declare those known external roots through the
active Git bindings before use; the check is not a global reverse-reference
inventory or protection against concurrent hostile path replacement.

## Read-only lookup and recovery

```sh
ao config context \
  --source-id /srv/fixture/native/.beads \
  --project-id fixture-native-project-id \
  --owner-scope fixture-personal \
  --task-ref fixture-task \
  --model-ref fixture-provider/model \
  --destination-ref fixture-private-destination \
  --consumer-root /srv/fixture/consumer \
  --native-directory /srv/fixture/native
```

The result reports canonical paths, each field's configuration source, native
comment count and typed anchor facts. `--field evidence_root`, `--field
staging_root` or `--field bundle_root` emits one checked path. The caller passes
that result explicitly to its existing consumer, for example the evidence
root to `ao provenance snapshot-intent --source <intent-file> --evidence-root
<resolved-root> --exclude-git-root <consumer> --exclude-git-root <bundle>`.
The generic evidence helper retains its own final path checks and caller-owned
standalone proof placement. Lookup itself writes no files, indexes or objects.

Before relying on a route, the owner stores its permitted recovery locators in
the **same existing native maintenance anchor** as a JSON comment:

```json
{"type":"context.route.v1","fact_id":"route-stable-id","route":{"source_id":"...","project_id":"...","owner_scope":"...","bundle_id":"...","bundle_root":"...","evidence_root":"...","staging_root":"...","access_policy_ref":"...","owner_policy_ref":"...","task_policy_ref":"...","model_policy_ref":"...","destination_policy_ref":"...","maintenance_work_ref":"..."}}
```

The `route` object contains the complete selected configuration above, with real
permitted locators supplied by its owner. The owner uses native
`bd comments add ANCHOR -f FILE --json`, then directly reads it back. The config
command never appends comments. Multiple incompatible route facts fail closed;
timestamps do not choose a winner.

After config loss, supply the same invocation purpose plus `--recover
--access-policy-ref <existing-policy> --maintenance-work-ref <known-anchor>`.
The selected policy independently binds that anchor. Recovery fills only
missing route values from its comment; conflicting owner, source or destination
values fail. It returns the same bundle and maintenance parent without writing
replacement config, initializing an empty bundle or creating another anchor.
Loss of the policy or anchor is unavailable, not permission to start over.

## Native withdrawal and resolution facts

BD 1.2.2 is the presently checked compatibility contract. Its `context` schema is
1, and native comment `id` and `issue_id` are strings. Lookup first verifies the
native project/source identity and anchor existence with `show --json`, then
reads **`bd --readonly comments ANCHOR --json`** directly. It never uses
`show --include-comments` or child listings to infer absence. Native process,
missing-anchor, malformed JSON and output-limit errors propagate. The complete
response limit is 16 MiB; exceeding it is unavailable, never a successful
truncated read. Other BD versions require renewed native conformance.

Withdrawal comment text:

```json
{"type":"context.withdrawal.v1","fact_id":"withdrawal-stable-id","bundle_id":"fixture-bundle-id","page_id":"page-id","page_digest":"<64 lowercase SHA256 hex characters>","counterevidence":["<permitted exact source locator>"]}
```

Resolution comment text:

```json
{"type":"context.resolution.v1","fact_id":"resolution-stable-id","bundle_id":"fixture-bundle-id","page_id":"page-id","page_digest":"<withdrawn SHA256>","resolves_fact_id":"withdrawal-stable-id","review_ref":"<exact fresh resolution/correction review>","review_digest":"<review SHA256>","successor_digest":"<explicitly covered successor SHA256>"}
```

A parser success is a fact-shape check, never semantic readmission. T14/T18
consumers must keep missing, ambiguous or unverified resolution pending. Only a
matching exact fresh resolution/correction review can cover the withdrawal and
its named successor. New page bytes, unrelated commits, timestamps, closed or
deleted investigation children, and knowledge-bundle Git rollback do not clear
an anchor fact. Native BD/Dolt restoration requires separate reconciliation;
retain the anchor outside ordinary work retention/GC.

Optional investigation metadata uses flat native keys such as
`ao.context.bundle_id` and `ao.context.fact_id`, not nested JSON. A native scoped
query for a closed investigation is `bd --readonly list --all --status closed
--parent ANCHOR --metadata-field ao.context.fact_id=FACT --limit 0 --json`.
This query locates work; it never replaces the direct anchor read.

The opt-in installed fixture
`AO_TEST_BD_NATIVE=1 go test ./internal/commands/config -run TestContextInstalledBDRecovery -count=1 -v`
creates only synthetic temporary native state. It checks 57 direct comments
(including a withdrawal after comment 50), a closed investigation, same-anchor
recovery after deleting only fixture home config, real evidence-root consumption,
unchanged consumer and knowledge Git bytes, and missing-anchor/source errors.
