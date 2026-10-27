# Sources and verification record

Research performed **2026-07-23** with targeted Parallel search/extract, official
PyPI JSON metadata, the PyTDC 1.1.15 source distribution, and an isolated import/API
smoke test. Web results were treated as untrusted text; only authoritative sources
below determined the skill.

## Release and package metadata

1. [PyTDC on PyPI](https://pypi.org/project/pytdc/)
   - Stable release: **1.1.15**
   - Uploaded: **2025-03-31**
   - Distribution: source tarball only, 154,168 bytes
   - SHA-256:
     `cd6164859af7b9b6f60e0c6d6e50679eacaffd09cfdea1acfc8bb7360e8e2205`
   - License metadata: MIT
   - No `Requires-Python` or Python classifiers
2. [PyPI JSON for 1.1.15](https://pypi.org/pypi/PyTDC/1.1.15/json)
   - Used to verify exact `Requires-Dist`, artifact metadata, and absence of
     `Requires-Python`.
3. [Official setup.py](https://github.com/mims-harvard/TDC/blob/main/setup.py)
   - Package name `pytdc`; version loaded from `tdc/version.py`; dependencies loaded
     from `requirements.txt`; no `python_requires`.
4. [Official requirements.txt](https://github.com/mims-harvard/TDC/blob/main/requirements.txt)
   - 1.1.15 pins/constrains a large dependency graph, including
     `cellxgene-census==1.15.0`, NumPy `<2`, RDKit `<2024.3.1`, Hugging Face
     packages, and TileDB-SOMA.
5. [cellxgene-census 1.15.0 JSON](https://pypi.org/pypi/cellxgene-census/1.15.0/json)
   - Declares `Requires-Python: >=3.8,<3.12`.
6. [RDKit 2023.9.6 JSON](https://pypi.org/pypi/rdkit/2023.9.6/json)
   - Provides CPython 3.8–3.12 wheels for common platforms, including macOS ARM64,
     but no CPython 3.13 wheel.
7. [Setuptools release history](https://setuptools.pypa.io/en/stable/history.html)
   - `pkg_resources` was deprecated long before this snapshot and removed in
     setuptools 82.0.0 (2026-02-08).
   - PyTDC 1.1.15 still imports it at runtime. The isolated smoke test therefore
     pins the verified compatibility release `setuptools==80.9.0`.

The pinned smoke environment uses CPython 3.11. PyTDC itself does not publish a
supported Python range, so this skill describes Python 3.11 plus setuptools 80.9.0
as the verified target rather than claiming broader upstream support. On the tested
macOS ARM64 resolver, the environment contained 123 packages and included large
Torch, RDKit, TileDB, Arrow, and scientific-Python artifacts.

## Official source used for API verification

1. [Package metadata registry](https://github.com/mims-harvard/TDC/blob/main/tdc/metadata.py)
   - Task/dataset names, evaluator names, oracle categories, benchmark names,
     benchmark metrics, and split metadata.
2. [Top-level public imports](https://github.com/mims-harvard/TDC/blob/main/tdc/__init__.py)
   - `Evaluator`, `Oracle`, and deprecated generic `BenchmarkGroup`.
3. [Single-prediction imports](https://github.com/mims-harvard/TDC/blob/main/tdc/single_pred/__init__.py)
4. [Multi-prediction imports](https://github.com/mims-harvard/TDC/blob/main/tdc/multi_pred/__init__.py)
5. [Generation imports](https://github.com/mims-harvard/TDC/blob/main/tdc/generation/__init__.py)
6. [Base loader](https://github.com/mims-harvard/TDC/blob/main/tdc/base_dataset.py)
7. [Single-prediction loader](https://github.com/mims-harvard/TDC/blob/main/tdc/single_pred/single_pred_dataset.py)
8. [Pair-prediction loader](https://github.com/mims-harvard/TDC/blob/main/tdc/multi_pred/bi_pred_dataset.py)
9. [General multi-prediction loader](https://github.com/mims-harvard/TDC/blob/main/tdc/multi_pred/multi_pred_dataset.py)
10. [Generation loader](https://github.com/mims-harvard/TDC/blob/main/tdc/generation/generation_dataset.py)
11. [Split implementations](https://github.com/mims-harvard/TDC/blob/main/tdc/utils/split.py)
12. [Evaluator implementation](https://github.com/mims-harvard/TDC/blob/main/tdc/evaluator.py)
13. [Oracle implementation](https://github.com/mims-harvard/TDC/blob/main/tdc/oracles.py)
14. [Download/load implementation](https://github.com/mims-harvard/TDC/blob/main/tdc/utils/load.py)
15. [Metadata retrieval helpers](https://github.com/mims-harvard/TDC/blob/main/tdc/utils/retrieve.py)
16. [Specialized BenchmarkGroup base](https://github.com/mims-harvard/TDC/blob/main/tdc/benchmark_group/base_group.py)
17. [Deprecated generic BenchmarkGroup](https://github.com/mims-harvard/TDC/blob/main/tdc/benchmark_deprecated.py)

The stable PyPI source distribution was inspected directly rather than assuming
that `main` or old generated documentation exactly matched 1.1.15.

## Official user documentation

1. [TDC quick start](https://tdcommons.ai/start/)
   - Problem/task/dataset hierarchy and constructor/get-data/get-split workflow.
2. [Dataset splits](https://tdcommons.ai/functions/data_split/)
   - Random defaults, documented scaffold scope, `cold_split` plus `column_name`,
     and combination split.
3. [Model evaluation](https://tdcommons.ai/functions/data_evaluation/)
   - Exact evaluator examples, input types, thresholds, and metric definitions.
4. [Benchmark/leaderboard guide](https://tdcommons.ai/benchmark/overview/)
   - `get`, `get_train_valid_split`, `evaluate`, `evaluate_many`, fixed test set,
     and at least five independent runs.
5. [ADMET benchmark group](https://tdcommons.ai/benchmark/admet_group/overview)
   - Dataset-specific benchmark metrics and scaffold protocol.
6. [Oracle documentation](https://tdcommons.ai/functions/oracles/)
   - Local, checkpoint, synthesis-service, and docking examples/requirements.
7. [Molecule generation task](https://tdcommons.ai/generation_tasks/molgen)
   - Stable MolGen names and random split examples.
8. [ADME task](https://tdcommons.ai/single_pred_tasks/adme)
   - Dataset-specific descriptions, splits, citations, and heterogeneous license
     labels.
9. [DTI task](https://tdcommons.ai/multi_pred_tasks/dti/)
   - DTI datasets, cold-drug/protein intent, and per-dataset licenses.
10. [Trial outcome task](https://tdcommons.ai/multi_pred_tasks/trialoutcome/)
    - Evidence that some TDC datasets carry non-commercial terms.
11. [TDC 0.4.1 ReadTheDocs](https://tdc.readthedocs.io/)
    - Generated API signatures and source links used only as a cross-check. Its
      displayed release is behind PyPI 1.1.15.
12. [Harvard Dataverse TDC collection](https://doi.org/10.7910/DVN/21LKWG)
    - Persistent collection identifier linked by the official README. The landing
      page was unavailable to the extraction service during this research, so file
      sizes/collection-level terms were not inferred from it.

## Primary TDC papers

1. Huang, K., Fu, T., Gao, W. *et al.* (2021).
   [Therapeutics Data Commons: Machine Learning Datasets and Tasks for Drug
   Discovery and Development](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/hash/4c56ff4ce4aaf9573aa5dff913df997a-Abstract-round1.html).
   NeurIPS Datasets and Benchmarks 2021. Published 2021-12-06.
   - Defines the original TDC task/dataset/benchmark/data-function scope.
2. Huang, K., Fu, T., Gao, W. *et al.* (2022).
   [Artificial intelligence foundation for therapeutic
   science](https://doi.org/10.1038/s41589-022-01131-2).
   *Nature Chemical Biology* 18, 1033–1036. Published 2022-09-21.
   - Describes the Commons as infrastructure for AI-ready tasks, datasets, and
     benchmarks across therapeutic science.

Papers support the Commons design and citation guidance; current Python signatures
come from package source and official API documentation.

## Confirmed migrations and removed stale guidance

- `from tdc import BenchmarkGroup` is implemented in
  `benchmark_deprecated.py` and prints a deprecation message. Prefer
  `from tdc.benchmark_group import admet_group` (or another specialized group).
- `group.get(name)` returns `train_val`, `test`, and normalized `name`; it is not
  indexed by seed.
- Multi-run input is a list of prediction dictionaries passed to
  `evaluate_many`, with at least five runs for non-docking groups.
- Generic cold split is `method="cold_split", column_name=...`.
  `cold_drug_target` is not implemented.
- Pair temporal split is `method="time", time_column=...`; `temporal` is not
  implemented.
- `stratified=True` is not a loader split argument.
- Registered Pearson correlation is `PCC`, not `Pearson`.
- Public generation imports are `MolGen`, `Reaction`, `RetroSyn`, and `SBDD`;
  `PairMolGen` is absent.

## Unresolved upstream uncertainty

1. **No changelog, tags, or GitHub Releases.** PyPI release history establishes
   version/date, but upstream does not document a complete 0.4.x → 1.1.x migration.
2. **Python support is undeclared.** `Requires-Python` is absent, while transitive
   pins constrain viable interpreters/platforms. Re-run resolver/import smoke tests
   before changing Python or platform.
3. **Legacy runtime dependency.** PyTDC still imports deprecated `pkg_resources`;
   environments with setuptools 82+ fail unless upstream migrates or setuptools is
   pinned to a compatible release.
4. **Unmarked backport dependency.** PyTDC requires the `dataclasses` backport on
   modern Python without an environment marker even though Python 3.11 includes
   `dataclasses` in the standard library. Strict resolvers may handle that stale
   metadata differently.
5. **ReadTheDocs lags PyPI.** It identifies as 0.4.1 while PyPI is 1.1.15.
6. **Website/source drift exists.** Some website snippets use old names or output
   comments; stable source controls exact executable behavior.
7. **Ambiguous dataset license labels.** Some pages render “Not Specified” next to a
   Creative Commons link. Resolve terms from the original provider rather than
   inferring a license.
8. **Evaluator metadata inconsistency.** `smina` appears in the evaluator registry,
   but 1.1.15 does not bind it in `Evaluator.assign_evaluator`.
9. **Oracle metadata understates side effects.** `logp` and `sa` are grouped with
   trivial oracles, but their stable implementations call `calculateScore`, which
   downloads the `fpscores` artifact when it is absent.
10. **Separate fork/package.** `pytdc-nextml` is a distinct package/repository and
   was not treated as an upgrade or replacement for official PyPI `PyTDC`.
