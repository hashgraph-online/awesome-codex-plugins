# Preservation Contract

| Outcome | Meaning |
| --- | --- |
| Hard failure | Protected type/value/count/order, Markdown structure, or number integrity changed |
| Manual hold | Claim, negation, modality, attribution, uncertainty, register, dialect, or code-switching may have drifted |
| Soft warning | Large shrinkage/expansion or residual diagnosed defect needs review |

Freeze fenced and inline code, commands, paths, URLs, identifiers, quotations, citations, headings, frontmatter, tables, names, dates, quantities, units, formulas, and user-designated immutable text when they matter to the task.

Use `⟦SIS:<run-tag>:<type>:<ordinal>⟧` for every frozen span. Choose a run tag absent from the source. Keep the reverse map task-local and discard it when the task ends. Restore exact type, value, count, and order.

Reject missing, duplicated, reordered, mutated, or unresolved placeholders. A hard failure blocks delivery. On a manual hold, preserve the original wording or report the unresolved risk. A soft warning allows one focused review, not unsupported rewriting.
