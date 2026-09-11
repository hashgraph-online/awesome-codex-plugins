# Selected OKF page profile

Use `ao provenance check-okf --file <concept.md>` to check the structure of one
caller-selected page. The default and only supported `--profile` is
`agentops-okf-v0.2/v1`, pinned to [OKF v0.2 SPEC at
ad30107c31c06aec8a7d5636e0d1058118604e6f](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md).
This is a stricter AgentOps authoring profile of ordinary UTF-8 Markdown and
YAML frontmatter, not a new knowledge syntax or a full bundle conformance test.
Upstream OKF makes most metadata optional; this selected profile requires the
fields below. `learning.coherence` does not establish this profile's validity.

The concrete consumer is the caller preparing a maintained reference or an
advisory candidate before exact-content review. The check catches missing or
malformed metadata; it does not decide whether prose is meaningful or supported.
Review this profile when its upstream pin or accepted caller contract changes;
retire it if no selected maintenance invocation consumes it.

## Required structure

The file begins with a `---` line, one YAML mapping, and a closing `---` line.
LF and CRLF line endings are accepted and the result hashes the original bytes.

| Field | Mechanical requirement |
|---|---|
| `type`, `title`, `description` | Nonempty strings. Unknown descriptive type values are accepted. |
| `status` | Explicit `draft`, `stable`, or `deprecated`. Omission never inherits upstream's implicit `stable`. |
| `sources` | Nonempty list of mappings, each with a nonempty string `resource`. Optional IDs are unique strings. Resources may be URLs, relative paths, or source scope descriptions. |
| `knowledge_use` | Producer metadata: `maintained-reference` or `promotion-candidate`. Neither value promotes a rule. |
| `applicability` | Nonempty string metadata or an `Applicability` section. |
| `claim` or `action` | At least one nonempty string or corresponding `Claim`/`Action` section. |
| `limitations` | Nonempty string metadata or a `Limitations` section. |
| `consumer` | Nonempty string metadata or a `Consumer` section naming the concrete user or invocation. |
| `retirement_condition` | Nonempty string metadata or a `Retirement condition` section describing when to review or withdraw the page. |

Named sections use standard ATX headings (`#` through `######`, case insensitive).
Headings inside fenced code or HTML comments do not supply required sections.
If a corresponding metadata key is present, it must itself be a nonempty string;
a body section cannot conceal malformed metadata. The checker confirms text is
present, not that it describes a useful consumer, valid claim or sufficient limit.

`agentops_profile`, if included as producer metadata, must match the selected
profile. A repeated `okf_version`, if present, must be the string `"0.2"`.
OKF's standard bundle version declaration lives in the root `index.md`; this
single-page check does not discover or read that file. The invoking caller
selects the pinned profile explicitly or uses the documented default. Unknown
or incompatible selections fail; no best-effort version fallback is applied.

Other producer keys are accepted without granting them authority. YAML duplicate
keys, aliases, merge inheritance, non-string mapping keys, nesting beyond 32
levels and more than 8,192 nodes are rejected to keep metadata explicit and
bounded. These are profile restrictions, not claims that all such YAML is
malformed under upstream OKF.

## Generated and verified metadata

Optional `generated` is a mapping with a required actor `by`; `at` is optional.
Optional `verified` accepts either one `{by, at}` mapping or a list of those
mappings. A present verification event requires both fields. Actors follow
`producer/version`, `human:id`, or `process:id`; strings alone establish no
independent process or factual review. Datetimes in these fields, `stale_after`
and `sources[].last_modified` use RFC3339 with an explicit UTC offset. An empty
verification list records no events and is accepted without a trust claim.

The checker does not execute computation or attestation fields, resolve source
links, evaluate stale dates, classify trust tiers, or prove any other optional
OKF family. Unknown extension values remain uninterpreted. Broken or unavailable
source targets need separate authorized review; structural success proves only
that their declared references have the required shape.

## Three separate decisions

Factual support, permission to disclose to the exact destination, and observed
usefulness remain distinct. A true page can be confidential; a permitted page
can be unused or harmful. Page status, owner/access labels and actor strings
cannot grant clearance, admission or semantic approval.

Prepare the final bytes, including any intended metadata, before independent
review. Reuse the existing exact-content manifest and `verdict.v2` mechanism;
keep matching factual-support and destination-disclosure judgments outside the
page under the caller's independently supplied expected acceptance. A batch may
cover every changed page and claim in one bounded review. Adding a stamp after
review changes the content digest and requires a new matching judgment.

Default retrieval still requires matching independent evidence-backed review
and current applicability. This structural command does not implement retrieval
or admission. Drafts and review outputs stay in caller-selected protected non-Git
staging until exact destination disclosure eligibility passes. Only approved
content may enter Git. Native runtime source/model/destination authorization
must precede page access; this parser is not an access-policy enforcement tool.

A narrowly supported observation from one episode may remain an observation or
maintained reference. General instructions and standing checks still need the
separate evidence and reapply proof owned by operationalize and pattern-mining.
Preserve null, harmful, failed and contradictory outcomes; schema validity and
retrieval counts do not demonstrate utility.

## Operation and output

The operation reads only the explicit regular `.md` concept file, at most 1 MiB,
with frontmatter ending within the first 64 KiB. It rejects file symlinks,
special files and reserved `index.md`/`log.md` pages. It does not traverse a
bundle, fetch citations, inspect Git or configuration, execute code, start a
model, schedule work, or write any file. Caller runtime/OS controls own actual
confinement; a same-user process or page label is not isolation.

JSON is the default; `--json`, `-o json`, and `-o yaml` provide structured output.
The result names the selected profile and upstream commit, exact input SHA-256,
`structurally_valid`, fixed field/code issues and an explicit assurance boundary.
It does not echo page prose, source locators or parser snippets. Exit 0 means
the selected structure is valid; exit 1 means findings, incompatible profile,
invalid input, read error or output failure. `--dry-run` performs the same
read-only check. Neither a successful exit nor `verified` metadata is a PASS.

The synthetic maintained-reference fixture is
`cli/internal/okfprofile/testdata/maintained-reference.md`; the table-driven
profile tests also cover narrow promotion candidates and negative examples.
It is illustrative test data, not knowledge admitted for retrieval.
