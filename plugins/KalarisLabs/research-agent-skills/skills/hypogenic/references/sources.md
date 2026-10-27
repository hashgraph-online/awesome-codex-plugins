# Dated sources

Research and access date: **2026-07-23**.

Only official project, package-index, repository, publisher, and provider
sources were used for behavioral claims. Parallel web search/extract identified
the canonical pages; GitHub and PyPI APIs were used to verify exact refs,
metadata, file hashes, and source files.

## Package and source

1. [PyPI: hypogenic](https://pypi.org/project/hypogenic/) — latest stable
   `0.3.5`, released 2025-07-16; Python requirement, beta classifier,
   dependencies, files, SHA-256 values, project links, trusted-publisher
   provenance, source tag/commit. Accessed 2026-07-23.
2. [ChicagoHAI/hypothesis-generation](https://github.com/ChicagoHAI/hypothesis-generation)
   — official repository, README, license, default branch, package layout,
   examples, task-config instructions, and current project links. Repository
   default commit checked 2026-07-23.
3. [Release v0.3.5 source tree](https://github.com/ChicagoHAI/hypothesis-generation/tree/8c3800ccae155e333fac5b530afa8abdaac38300)
   — immutable source used for API/CLI review. Commit dated 2025-07-16; accessed
   2026-07-23.
4. [GitHub releases](https://github.com/ChicagoHAI/hypothesis-generation/releases)
   — release/tag history through `v0.3.5`. Accessed 2026-07-23.
5. [Master commit history](https://github.com/ChicagoHAI/hypothesis-generation/commits/master)
   — four post-tag logging/debug commits ending at
   `bd37a3129a2f98ee586f545a57b10b59496eedad` on 2025-07-17. Accessed
   2026-07-23.
6. [Pinned pyproject.toml](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/pyproject.toml)
   — version, Python requirement, dependencies, optional `dev` dependencies,
   console entry points, license, and project URLs. Accessed 2026-07-23.
7. [Pinned generation CLI](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic_cmd/generation.py)
   and [inference CLI](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic_cmd/inference.py)
   — exact parser flags, defaults, execution flow, logging, output, and metric
   behavior. Accessed 2026-07-23.
8. [Pinned task loader](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/tasks.py)
   and [prompt implementation](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/prompt.py)
   — YAML fields, split-path resolution, sampling, and prompt-template access.
   Accessed 2026-07-23.
9. [Pinned model wrappers](https://github.com/ChicagoHAI/hypothesis-generation/tree/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/LLM_wrapper)
   — OpenAI, Anthropic, Transformers, vLLM, local registration, cost table, and
   model-loading behavior. Accessed 2026-07-23.
10. [Pinned output serializer](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/algorithm/update/base.py)
    and [SummaryInformation](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/algorithm/summary_information.py)
    — hypothesis-bank JSON shape and stored statistics. Accessed 2026-07-23.
11. [Pinned Redis cache](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/LLM_cache.py)
    — local Redis prompt/response caching and pickle serialization. Accessed
    2026-07-23.

## Datasets

12. [ChicagoHAI/HypoBench-datasets](https://github.com/ChicagoHAI/HypoBench-datasets)
    — current official GitHub data/config repository; no releases. Default
    revision `7e4bbc341ee90b7efaa607f67a81543cd68cdf2e`, dated 2025-07-09;
    accessed 2026-07-23.
13. [Pinned HypoBench dataset tree](https://github.com/ChicagoHAI/HypoBench-datasets/tree/7e4bbc341ee90b7efaa607f67a81543cd68cdf2e)
    — task families, configs, and split files used for the manifest example.
    Accessed 2026-07-23.
14. [ChicagoHAI/HypoGeniC-datasets on Hugging Face](https://huggingface.co/datasets/ChicagoHAI/HypoGeniC-datasets)
    — official alternate dataset publication. Observed revision
    `613860dcbcda9e522a6163ee9edf78c261ebe4bb`, last modified 2025-04-23;
    accessed 2026-07-23.

## Papers and evaluation scope

15. [Hypothesis Generation with Large Language Models](https://aclanthology.org/2024.nlp4science-1.10/)
    — Zhou et al., Proceedings of the 1st Workshop on NLP for Science,
    November 2024, DOI `10.18653/v1/2024.nlp4science-1.10`. Data-driven
    HypoGeniC algorithm, classification evaluations, and paper claims.
    Accessed 2026-07-23.
16. [Literature Meets Data: A Synergistic Approach to Hypothesis Generation](https://arxiv.org/abs/2410.17309)
    — Liu et al.; submitted 2024-10-22, version 3 dated 2025-01-08.
    HypoRefine, literature/data integration, union methods, five-dataset
    evaluation, and human decision-support study. Accessed 2026-07-23.
17. [HypoBench: Towards Systematic and Principled Benchmarking for Hypothesis Generation](https://arxiv.org/abs/2504.11524)
    — Liu et al.; submitted 2025-04-15, version 2 dated 2026-02-10. Seven
    real-world tasks, five synthetic task families, 194 datasets, evaluation
    dimensions, and documented remaining limitations. Accessed 2026-07-23.
18. [HypoBench OpenReview record](https://openreview.net/forum?id=cizEoSePyT)
    — TMLR submission metadata and revisions; submitted 2025-08-31, modified
    2026-02-25, recorded as rejected. Used only to distinguish publication
    status from the arXiv version. Accessed 2026-07-23.

## Provider authentication and privacy

19. [OpenAI developer quickstart](https://developers.openai.com/api/docs/quickstart)
    — `OPENAI_API_KEY` and automatic SDK environment lookup. Accessed
    2026-07-23.
20. [OpenAI enterprise privacy](https://openai.com/enterprise-privacy/) —
    business/API training defaults, up-to-30-day API retention, exceptions, and
    eligible ZDR requests. Page search result dated 2026-01-08; accessed
    2026-07-23.
21. [Anthropic get started](https://docs.anthropic.com/en/docs/get-started) —
    `ANTHROPIC_API_KEY` and automatic SDK environment lookup. Accessed
    2026-07-23.
22. [Anthropic API and data retention](https://docs.anthropic.com/en/docs/build-with-claude/zero-data-retention)
    — standard policy links, eligible ZDR, feature exclusions, legal/misuse
    exceptions, HIPAA readiness, and model-specific retention. Accessed
    2026-07-23.
23. [Anthropic commercial data retention](https://privacy.anthropic.com/en/articles/7996866-how-long-do-you-store-personal-data)
    — automatic API input/output deletion within 30 days. Updated 2026-07-01;
    accessed 2026-07-23.
24. [Anthropic covered-model retention](https://support.claude.com/en/articles/15425996-data-retention-practices-for-covered-models)
    — 30-day retention requirement for designated covered models, including
    effects on ZDR arrangements. Updated 2026-07-09; accessed 2026-07-23.

## Local model behavior

25. [Transformers installation and offline mode](https://huggingface.co/docs/transformers/installation)
    — Hub downloads, caches, pre-download workflows, and local reload. Accessed
    2026-07-23.
26. [Transformers pipelines](https://huggingface.co/docs/transformers/en/main_classes/pipelines)
    — model/path loading and `trust_remote_code` warning. Accessed 2026-07-23.
