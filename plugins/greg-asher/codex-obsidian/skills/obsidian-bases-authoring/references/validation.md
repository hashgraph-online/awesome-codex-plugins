# Bases authoring verification

Run `python3 -B -m unittest discover -s skills/obsidian-bases-authoring/tests`. Creation tests use the standard library. Run again in a Python 3.9+ environment with PyYAML 6 to include scoped edit tests. They cover typed filters, unknown and circular formula references, literal escaping, incompatible summaries, malformed YAML, ambiguous views, and byte preservation for unrelated fields.

For a live run, copy the [dashboard collection](../assets/fixtures/dashboard/) into a disposable registered vault. Resolve the exact collection and target and sample properties before applying [the dashboard request](../assets/fixtures/dashboard-request.json). Treat the named table's expected results independently from syntax validation.

| Open work row in due-date order | Status | Owner | Weighted hours |
| --- | --- | --- | ---: |
| Redirect review | blocked | Ana | 6 |
| Outage rehearsal | open | João | 10 |
| Confirm ownership | open | Missing | 4 |

Staging approval is done, Unclassified has no status, and Catering is outside the collection. Open work omits all three. All work includes the five Markdown notes in the folder. The two group totals are 6 and 14. The overall sum is 20.

## Live disposable-vault evidence

- Official Obsidian desktop CLI and installer 1.15.0 on macOS created and overwrote the exact `.base` paths through the bundled launcher. Raw bytes matched the candidates. The new dashboard opened and the active `base:views` listed both tables. A path argument to `base:views` did not pin a target on this build. Pinned named `base:query` was used for all row assertions.
- Live queries matched exact row paths, due-date order, missing owner, exclusions, and formula cells. Numeric formula values were represented as strings in CLI JSON. An additional typed date-filter probe included Staging approval and Redirect review through November 6. The rendered table exposed blocked and open group headers and native Sum values 6, 14, and 20 in the app. These native UI observations are separate from the derived sum of CLI rows.
- The existing YAML fixture had an unrelated table, hand-tuned column size, comments, and extension fields at both document and view levels. A stale edit stopped before dispatch after an intervening change. A fresh approved edit changed the selected table's order and sort, retained the other bytes and untouched view results, and left source notes byte-identical.
- The project baseline used the Atlas authentication rollout decisions and open work as a representative set. The renderer replaced manual table, filter and formula setup. Manual review identified an unassigned owner and an unclassified note. The final open view kept the missing owner visible and excluded the missing status explicitly, while the All work view retained it for review.
- A refreshed local Codex marketplace install routed `base.dashboard` to the installed skill, checked five live source notes, and generated the exact no-write preview. A controlled CLI apply saved that draft byte-for-byte, and its named view returned the same three ordered rows, missing owner, and calculated values.
