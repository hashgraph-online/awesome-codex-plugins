# Workflow Notes

Use this file when the task needs a little more than the minimal scaffold.

## Build a clean request

Follow this order:

1. Create the client.
2. Define a `genome.Interval` that covers the locus of interest.
   - For `predict_variant(...)`, use a supported width (currently `16384`, `131072`, `524288`, or `1048576` bp).
3. Define a `genome.Variant` when the task is about allelic effects.
4. Ask for the narrowest set of outputs that answers the question.
5. Add `ontology_terms` only when the modality depends on anatomical or tissue context.

Keep the code small until the first successful prediction returns.
Keep API keys in environment variables, and do not print them in logs or notebook outputs.

## Choose the analysis style

Use a variant workflow when the user asks for:

- reference-versus-alternate comparisons
- variant effect interpretation
- plots with a highlighted mutation

Use extra caution when the user asks for interval-only predictions. The README explains the capability, but the bundled grounded code sample only shows `predict_variant(...)`. Confirm the exact interval-only call from the installed package or official docs before writing final code.

## Plot reference and alternate tracks

Use plotting only after a prediction succeeds:

```python
from alphagenome.visualization import plot_components
import matplotlib.pyplot as plt

plot_components.plot(
    [
        plot_components.OverlaidTracks(
            tdata={
                "REF": outputs.reference.rna_seq,
                "ALT": outputs.alternate.rna_seq,
            },
            colors={"REF": "dimgrey", "ALT": "red"},
        ),
    ],
    interval=outputs.reference.rna_seq.interval,
    annotations=[plot_components.VariantAnnotation([variant], alpha=0.8)],
)
plt.show()
```

If the user does not ask for a figure, stop at the prediction object and explain how to inspect it.

## Real-run artifact contract (recommended)

For agent-driven real execution, prefer writing both:

- one plot file (REF vs ALT overlay), and
- one JSON summary with run status and key parameters.

Suggested summary keys:

- `run_time_utc`, `env_prefix`, `alphagenome_version`
- `assembly`, `chrom`, `position`, `ref`, `alt`
- `interval_start`, `interval_end`, `interval_width`
- `requested_outputs`, `ontology_terms`
- `status`, `error`, `plot_path`, `summary_path`

This makes retries and automated evaluation deterministic.

## State assumptions explicitly

Call out every inferred choice:

- chromosome and coordinate window
- reference and alternate alleles
- output modality
- ontology term

If any of these are missing, prefer placeholders or a short clarification over guessing silently.
