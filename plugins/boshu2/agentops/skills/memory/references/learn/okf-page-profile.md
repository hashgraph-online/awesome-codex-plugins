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

The command reads one file and writes nothing. Exit 0 means the selected
structure is valid; its JSON names each missing or malformed field. Neither a
successful exit nor `verified` metadata is factual review or a PASS: admission
follows [Memory rule 4](../../SKILL.md#rules-for-any-saved-lesson-or-rule).
