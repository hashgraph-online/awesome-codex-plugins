<!--
Copyright (c) 2026 The State Key Laboratory of Blockchain and Data Security, Zhejiang University
SPDX-License-Identifier: Apache-2.0
-->

---
name: guixu
description: "Dataset discovery, valuation, and acquisition for AI training. Use when: (1) finding datasets for model training or fine-tuning, (2) evaluating dataset quality and relevance, (3) downloading datasets from Kaggle, HuggingFace, IPFS, or other sources, (4) assessing dataset licensing and provenance, (5) acquiring paid or free datasets. NOT for: generic web search (use browser), local file operations (use file tools), or data labeling/annotation tasks."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["guixu"] },
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "guixu",
              "bins": ["guixu"],
              "label": "Install Guixu CLI (brew)",
            },
          ],
      },
  }
---

# Guixu Data Agent

Guixu provides dataset discovery, valuation, and acquisition for AI agents.
It searches across Kaggle, HuggingFace, IPFS, arXiv, DBLP, and other sources.

## When to Use

✅ **USE this skill when:**

- User asks to "find a dataset for training..."
- User asks to "download a dataset about..."
- User asks to "evaluate dataset quality..."
- User asks about dataset licensing or provenance
- User mentions specific datasets (Kaggle, HuggingFace, etc.)
- User wants to search for training data

❌ **DON'T use this skill when:**

- Generic web search → use browser or web search tools
- Local file read/write → use file tools
- Data labeling or annotation → use coding tools
- Code implementation questions → use coding-agent skill

## Workflow

### Step 1: Parse Intent (REQUIRED first)

Always start with `intent_parse` to structure the request:

```
intent_parse(query="find me a cat image dataset for classification", task_type="classification")
```

This returns a structured `QueryProfile` with:
- `task_type`: classification, detection, segmentation, etc.
- `keywords`: dataset content terms
- `target_entity`: main subject
- `data_standard`: sample_unit, budget, schema expectations

### Step 2: Search Datasets

Use `dataset_search` with keywords from intent_parse:

```
dataset_search(query="cat image", task_type="classification", limit=10)
```

Supported sources (leave empty to search all):
- `kaggle`, `huggingface`, `ipfs`, `bittorrent`
- `arxiv`, `dblp`, `semanticscholar`
- `defillama`, `rwa_xyz`, `guixu-hub`
- `pansearch` (cloud drives)

Filter options:
- `filters.max_price`: maximum price in USD
- `filters.free_only`: only free datasets
- `filters.license`: specific license (e.g., "CC-BY-4.0")

### Step 3: Evaluate Candidates

For each promising candidate, call `dataset_evaluate`:

```
dataset_evaluate(cid="kaggle:owner/dataset-name", task_description="cat image classification", task_type="classification", required_columns=["image_path", "label"])
```

This returns:
- `tcv_score`: -100 (harmful) to +100 (highly valuable)
- `schema_fit`: compatibility with required columns
- `community_signal`: reviews and ratings

### Step 4: Download

Once a dataset is selected:

```
dataset_download(cid="kaggle:owner/dataset-name")
# or
dataset_download(cid="hf:owner/dataset-name")
```

Free sources: `uci:`, `openml:`, `zenodo:`, `figshare:`, `hf:` (public), `ipfs:`, `guixu-hub:`
Requires login: `kaggle:`

## Tool Chaining Examples

### Classification Dataset

```
1. intent_parse(query="find me a dog vs cat classification dataset", task_type="classification")
2. dataset_search(query="cat dog classification", task_type="classification", limit=10)
3. dataset_evaluate(cid="kaggle:username/dataset", task_description="dog cat binary classification", task_type="classification", required_columns=["image_path", "label"])
4. dataset_download(cid="kaggle:username/dataset")
```

### Detection Dataset

```
1. intent_parse(query="find helmet detection dataset with bounding boxes", task_type="detection")
2. dataset_search(query="helmet detection bounding box", task_type="detection", limit=10)
3. For each candidate: dataset_evaluate(cid, task_description="helmet detection", task_type="detection", required_columns=["image_path", "bbox"])
4. Download best candidate
```

### Tabular Finance Dataset

```
1. intent_parse(query="find stock price dataset for time series forecasting", task_type="forecasting")
2. dataset_search(query="stock price time series", task_type="forecasting", filters={source: "defillama"})
3. dataset_evaluate(cid, task_description="stock price prediction", task_type="forecasting", required_columns=["timestamp", "price"])
4. dataset_download(cid)
```

## Important Notes

- **Always call `intent_parse` FIRST** — it extracts task_type and keywords that improve search quality
- **Keywords should be CONTENT only** — no task words like "classification" or "detection"
- **Check license before purchase** — use `require_license_review: true` in evaluation
- **Budget enforcement** — set `filters.max_price` or `budget` to limit spending
- **Free sources first** — try `guixuhub`, `huggingface`, `ipfs` before paid sources

## Error Handling

If `dataset_search` returns no results:
- Try broader keywords
- Remove source filters
- Check if the source is spelled correctly

If `dataset_evaluate` fails:
- Dataset may be unavailable
- Try a different candidate

If `dataset_download` fails:
- Check if login is required (Kaggle)
- Verify the CID format is correct: `source:owner/dataset`
