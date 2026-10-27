---
name: benchling-integration
description: Benchling Python SDK and REST API integration for registry entities, inventory, ELN entries, workflows, Benchling Apps, and Data Warehouse queries. Use when automating lab data with benchling-sdk or the v2 API.
license: MIT
compatibility: Requires a Benchling account, tenant URL, and API key or OAuth app credentials. Install benchling-sdk with uv pip install.
allowed-tools: Read Write Edit Bash
metadata:
  version: '1.5'
  category: lab-automation
  maintainer: Kalaris Labs
  openclaw:
    primaryEnv: BENCHLING_API_KEY
    envVars:
    - name: BENCHLING_TENANT_URL
      required: true
      description: Benchling tenant base URL.
    - name: BENCHLING_API_KEY
      required: false
      description: API key auth (alternative to OAuth).
    - name: BENCHLING_CLIENT_ID
      required: false
      description: OAuth app client id.
    - name: BENCHLING_CLIENT_SECRET
      required: false
      description: OAuth app client secret.
    - name: BENCHLING_PROD_TENANT_URL
      required: false
      description: Production tenant URL (multi-env setups).
    - name: BENCHLING_PROD_API_KEY
      required: false
      description: Production API key (multi-env setups).
    - name: BENCHLING_STAGING_TENANT_URL
      required: false
      description: Staging tenant URL (multi-env setups).
    - name: BENCHLING_STAGING_API_KEY
      required: false
      description: Staging API key (multi-env setups).
  tags: Benchling, electronic lab notebook, LIMS, lab automation, biotech
---

# Benchling Integration

## Overview

Benchling is a cloud platform for life sciences R&D. Access registry entities (DNA, RNA, proteins), inventory, electronic lab notebooks, and workflows programmatically via the Python SDK and REST API.

**Version note:** Examples target **benchling-sdk 1.25.0** (latest stable on PyPI). Docs: [benchling.com/sdk-docs](https://benchling.com/sdk-docs/). Platform guide: [docs.benchling.com](https://docs.benchling.com/).

## When to Use This Skill

This skill should be used when:
- Working with Benchling's Python SDK or REST API
- Managing biological sequences (DNA, RNA, proteins) and registry entities
- Automating inventory operations (samples, containers, locations, transfers)
- Creating or querying electronic lab notebook entries
- Building workflow automations or Benchling Apps
- Syncing data between Benchling and external systems
- Querying the Benchling Data Warehouse for analytics
- Setting up event-driven integrations with AWS EventBridge

## Core Capabilities

Seven capability areas, each with code, are in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Authentication and setup** — API key and OAuth app auth; see
   [references/authentication.md](references/authentication.md).
2. **Registry and entity management** — DNA and AA sequences, custom entities, schemas,
   and registration.
3. **Inventory management** — containers, boxes, plates, locations, and transfers.
4. **Notebook and documentation** — entries, day-to-day notes, and structured tables.
5. **Workflows and automation** — tasks, flowcharts, and assay runs.
6. **Events and integration** — EventBridge subscriptions; see
   [references/eventbridge.md](references/eventbridge.md).
7. **Data warehouse and analytics** — SQL access to the warehouse.

Endpoint and SDK detail is in
[references/api_endpoints.md](references/api_endpoints.md) and
[references/sdk_reference.md](references/sdk_reference.md).

## Best Practices

### Error Handling

The SDK automatically retries failed requests:
```python
# Automatic retry for 429, 502, 503, 504 status codes
# Up to 5 retries with exponential backoff
# Customize retry behavior if needed
from benchling_sdk.retry import RetryStrategy

benchling = Benchling(
    url=tenant_url,
    auth_method=ApiKeyAuth(api_key),
    retry_strategy=RetryStrategy(max_retries=3),
)
```

### Pagination Efficiency

Use generators for memory-efficient pagination:
```python
# Generator-based iteration
for page in benchling.dna_sequences.list():
    for sequence in page:
        process(sequence)

# Check estimated count without loading all pages
total = benchling.dna_sequences.list().estimated_count()
```

### Schema Fields Helper

Use the `fields()` helper for custom schema fields:
```python
# Convert dict to Fields object
custom_fields = benchling.models.fields({
    "concentration": "100 ng/μL",
    "date_prepared": "2025-10-20",
    "notes": "High quality prep"
})
```

### Forward Compatibility

The SDK handles unknown enum values and types gracefully:
- Unknown enum values are preserved
- Unrecognized polymorphic types return `UnknownType`
- Allows working with newer API versions

### Security Considerations

- Never commit API keys or OAuth secrets to version control
- Read only named environment variables (`BENCHLING_TENANT_URL`, `BENCHLING_API_KEY`, etc.)
- Route network calls exclusively to your tenant URL
- Rotate keys if compromised; use OAuth for multi-user production apps
- Grant minimal necessary permissions for apps in the Developer Console

## Resources

### references/

Detailed reference documentation for in-depth information:

- **authentication.md** - Comprehensive authentication guide including OIDC, security best practices, and credential management
- **sdk_reference.md** - Detailed Python SDK reference with advanced patterns, examples, and all entity types
- **api_endpoints.md** - REST API endpoint reference for direct HTTP calls without the SDK
- **eventbridge.md** - EventBridge setup, event payload schema, rule examples, Lambda handler, validation, and recovery

Load these references as needed for specific integration requirements.

## Common Use Cases

**1. Bulk Entity Import:**
```python
# Import multiple sequences from FASTA file
from Bio import SeqIO

for record in SeqIO.parse("sequences.fasta", "fasta"):
    benchling.dna_sequences.create(
        DnaSequenceCreate(
            name=record.id,
            bases=str(record.seq),
            is_circular=False,
            folder_id="fld_abc123"
        )
    )
```

**2. Inventory Audit:**
```python
# List all containers in a specific location
containers = benchling.containers.list(
    parent_storage_id="box_abc123"
)

for page in containers:
    for container in page:
        print(f"{container.name}: {container.barcode}")
```

**3. Workflow Automation:**
```python
# Update all pending tasks for a workflow
tasks = benchling.workflow_tasks.list(
    workflow_id="wf_abc123",
    status="pending"
)

for page in tasks:
    for task in page:
        # Perform automated checks
        if auto_validate(task):
            benchling.workflow_tasks.update(
                task_id=task.id,
                workflow_task=WorkflowTaskUpdate(
                    status_id="status_complete"
                )
            )
```

**4. Data Export:**
```python
# Export all sequences with specific properties
sequences = benchling.dna_sequences.list()
export_data = []

for page in sequences:
    for seq in page:
        if seq.schema_id == "target_schema_id":
            export_data.append({
                "id": seq.id,
                "name": seq.name,
                "bases": seq.bases,
                "length": len(seq.bases)
            })

# Save to CSV or database
import csv
with open("sequences.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
    writer.writeheader()
    writer.writerows(export_data)
```

## Additional Resources

- **Official Documentation:** https://docs.benchling.com
- **Python SDK Reference:** https://benchling.com/sdk-docs/
- **API Reference:** https://benchling.com/api/reference
- **Support:** [email protected]

## Agent operating procedure

1. **Check the environment.** Confirm the instrument or platform model, API version, credentials and whether a simulator is available.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Simulate the protocol or run it with water or dummy labware before using real samples.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Verify volumes, deck layout and labware definitions; have a human approve the protocol before execution.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| The protocol fails in simulation | Fix it in simulation; never run an unvalidated protocol on hardware. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Never trigger physical actions, orders or charges without explicit user confirmation.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `labarchive-integration`: Securely integrate with the official LabArchives ELN REST-like API and Inventory API v1.
- `latchbio-integration`: Build, register, debug, and operate bioinformatics workflows on Latch using the Python SDK, CLI, Latch Data and Registry, Nextflow, Snakema…
