# Upstream package, source, CLI, and workflows

Research date: 2026-07-23.

## Release and integrity status

The latest stable PyPI artifact is `hypogenic==0.3.5`, uploaded
2025-07-16. PyPI metadata declares Python `>=3.10`, MIT, and Development Status
4 (Beta). Both files are non-yanked:

- wheel: `hypogenic-0.3.5-py3-none-any.whl`, 96,169 bytes,
  SHA-256
  `f4ee8d7fa433cd59c58e0a8fe7df2f481ae29e7465a1b30ccbdac2c216a1b755`;
- sdist: `hypogenic-0.3.5.tar.gz`, 65,423 bytes, SHA-256
  `5e1e5590f3612cb606a669909aab117d66577cf078dd56cae0f4123c5e8c44ae`.

PyPI trusted-publisher attestations identify repository
`ChicagoHAI/hypothesis-generation`, tag `v0.3.5`, commit
`8c3800ccae155e333fac5b530afa8abdaac38300`, and the repository's
`publish-to-pypi.yml` workflow. This is sufficient to recommend a pinned PyPI
install, while still requiring ordinary lockfile/hash controls.

The default `master` commit observed was
`bd37a3129a2f98ee586f545a57b10b59496eedad` (2025-07-17). It is four commits
ahead of the release tag; the changed files add logging/visualization support
and a debug option. The `README.md` and `pyproject.toml` blobs are identical
between `v0.3.5` and that master revision, and the source version remains
`0.3.5`. No newer GitHub release or PyPI version was found.

Interpretation: artifact, source tag, metadata, and README provenance align.
The branch has small unreleased logging changes, so do not substitute branch
tip for the release.

## Declared dependency surface

The default artifact declares broad compatible-release ranges around:

- NumPy 1.26.3, pandas 2.1.4, datasets 2.16.1;
- Transformers 4.45.1, PyTorch 2.4.0, Accelerate 0.33.0;
- OpenAI 1.40.3, Anthropic 0.32.0, Redis 5.0.1;
- scikit-learn 1.3.0, matplotlib 3.8.0, PuLP 2.9.0;
- PyYAML 6.0.1 and several document/web packages.

The `dev` extra adds vLLM 0.6.2 and `vllm-flash-attn` 2.6.2. Resolve this in an
isolated environment. The package declaration says Python `>=3.10` but does not
state an upper bound; actual resolver/platform support is constrained by those
older compiled dependencies.

## Verified import and registry surface

The package root does not export `BaseTask`. The source imports used by its own
examples include:

```python
from hypogenic.tasks import BaseTask
from hypogenic.prompt import BasePrompt
from hypogenic.extract_label import extract_label_register
from hypogenic.LLM_wrapper import llm_wrapper_register
```

These are source-level interfaces in 0.3.5, not a separately versioned public
API contract. Prefer the pinned examples when writing custom code.

Registered model wrapper types:

- `gpt`: OpenAI Python client and chat-completions calls;
- `claude`: Anthropic Python client and Messages calls;
- `huggingface`: local Transformers text-generation pipeline;
- `vllm`: local vLLM generation.

Important local-provider limitation: `hypogenic.LLM_wrapper.__init__` imports
both local wrappers from one module, and that module raises when `vllm` is
absent. The exception is caught, leaving both `huggingface` and `vllm`
unregistered. Thus the base install's CLI advertises both choices, but local
wrapper registration depends on the `dev` path in this release.

The hosted wrappers instantiate `OpenAI()` and `Anthropic()` without an
explicit key, so their SDK-standard names are `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY`. No other credential names were found in the wrapper code.

## CLI entry points and limitations

`pyproject.toml` declares:

```text
hypogenic_generation = hypogenic_cmd.generation:main
hypogenic_inference  = hypogenic_cmd.inference:main
```

Use their pinned `--help` output as the command contract. Do not copy the old
skill's `--config`, `--method`, `--num_hypotheses`, `--hypotheses`,
`--test_data`, or `--papers` examples; those flags are not present in the
0.3.5 entry-point parsers.

Verified generation options include:

- `--task_config_path`, `--model_name`, `--model_path`, `--model_type`;
- train/validation/test counts and seed;
- bank size, initialization, update, replacement, concurrency, Redis/cache,
  output, restart, and logging options;
- `max_tokens` and `temperature` are accidentally declared as positional
  arguments despite having defaults. Treat them as required by this parser and
  confirm with `--help`.

Verified inference options include:

- `--task_config_path`, `--hypothesis_file`, provider/model options;
- seeds, split counts, validation switch, inference style, adaptive settings,
  cache/Redis, concurrency, logging, token cap, and temperature.

Known source quirks relevant to reproducibility:

- generation defaults combine `model_type=gpt` with a Meta-Llama model name;
  defaults are not a safe executable plan;
- importing the generation entry-point module on Python 3.13 emits a
  `SyntaxWarning` for an invalid `\{` escape in one help string;
- the GPT wrapper's embedded cost table has only `gpt-4o-mini`, `gpt-4o`,
  `o1`, and `o3-mini`, and uses direct lookup. It is not current pricing or
  general model support;
- generation has a TODO instead of reporting session cost;
- the inference entry point computes per-seed accuracy/F1 but does not append
  them to its averaging lists, so its final averaged log values are not
  reliable;
- the README says new-task command-line support is planned for a later release;
- the README's generic task snippet swaps validation/test filenames, while
  pinned dataset configs use distinct, correctly named split files.

These mismatches are why this skill provides planning/auditing tools but does
not auto-run the upstream CLI.

## Task and dataset support

The label-extractor registry contains handlers for:

- default, AI-generated-content detection, headline comparison, deceptive
  reviews, retweets, shoe color, Yelp rating, persuasive pairs, Dreaddit stress,
  election, preference, and admission tasks.

A registered label parser is not proof of complete end-to-end task support.
The current HypoBench dataset repository covers seven real-world task families
(deception, AI-content detection, persuasive arguments, mental stress,
headline engagement, retweets, and paper citations) plus synthetic task
families and variants. Use the config included with the exact pinned dataset
revision.

Dataset JSON is column-oriented: every field maps to a list and all lists must
have equal length. `BaseTask` joins each configured path to the task config's
directory, samples rows, and returns pandas data frames. Train, validation,
test, and optional OOD files remain distinct only if the config preserves them.

## Generation, outputs, and evaluation

Default HypoGeniC:

1. creates candidate hypotheses from batches of labeled training examples;
2. evaluates hypotheses through LLM-based label inference;
3. updates accuracy/reward/visit statistics;
4. generates replacements after accumulated difficult examples;
5. writes intermediate/final banks.

The saved bank is a JSON object keyed by hypothesis text. Each value serializes
`SummaryInformation`:

```json
{
  "hypothesis": "candidate text",
  "acc": 0.0,
  "reward": 0.0,
  "num_visits": 0,
  "correct_examples": []
}
```

Literature/HypoRefine examples additionally preprocess supplied PDFs, summarize
papers, refine data/literature hypotheses, and create HypoRefine,
literature-only, and union banks. This is an example-script workflow rather
than a `--method hyporefine` flag on the packaged generation entry point.

Default inference sorts the bank by stored accuracy, applies the best entry to
the selected split, and returns prediction/label lists internally. The CLI
logs per-seed accuracy, F1, and wrong indices; it does not define the strict
result artifact used by this skill. `assets/result.example.json` is a
skill-local, model-free interchange schema.

The upstream papers evaluate classification utility, human decision support,
generalization, and hypothesis-discovery behavior. Those evaluations do not
turn generated text into causal or experimentally confirmed scientific
evidence.
