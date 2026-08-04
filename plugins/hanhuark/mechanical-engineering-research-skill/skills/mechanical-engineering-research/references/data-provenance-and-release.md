# Data Provenance, Benchmarks, And Research Release

Use this reference for research datasets, reproducibility packages, benchmark design, public repositories, archival releases, data rights, and community databanks.

## Provenance Contract

Separate raw, processed, derived, simulated, synthetic, and presentation data. Keep raw data immutable when possible.

For each source or artifact, record:

- stable source identifier, provider, version, date, geography or facility, and checksum;
- evidence class and acquisition or simulation method;
- schema, units, coordinate and time bases, missing-value conventions, and data ordering;
- transformation lineage, code version, environment, parameters, and generated outputs;
- quality flags, uncertainty, validation state, and applicability;
- owner, license, attribution, access class, publication permission, redistribution permission, embargo, and review state.

Use [data-rights-manifest.csv](../assets/templates/data-rights-manifest.csv) for rights decisions. Do not assume that rounding, aggregation, hashing, encryption, or packaging makes a licensed derivative redistributable.

## Reproducibility Package

Provide, in proportion to maturity:

- a clear intended user and decision;
- README with inputs, outputs, environment, commands, and limitations;
- one verified end-to-end baseline example;
- source data pointers and immutable versions;
- processing, analysis, figure, and table generation commands;
- tests or smoke checks and their results;
- citation, license, version, release tag, and archive DOI when available;
- a manifest linking released outputs to code, environment, and input hashes.

Apply a stranger test in a clean supported environment when claiming public usability. A GUI is optional; add one only when it removes a demonstrated barrier and remains consistent with the CLI or API.

## Benchmark Dataset Design

Treat a small initial release as a seed benchmark unless it already provides sufficient coverage, governance, and external validation.

Include:

- raw and prepared data with traceable transformations;
- acquisition and physics metadata;
- synchronization and coordinate-registration records for multimodal data;
- immutable train/validation/test splits and leakage rules;
- run-, specimen-, geometry-, fluid-, pressure-, facility-, or operating-path-held-out generalization axes as relevant;
- baseline models, metrics, uncertainty, and failure cases;
- external-data rules and leaderboard governance;
- versioning, DOI/archive plan, contribution guide, and maintenance owner.

Use [benchmark-dataset-readme.md](../assets/templates/benchmark-dataset-readme.md) as a starting structure.

## Physics Metadata And Curation

Record ordinary catalog metadata plus geometry, fluid/material, pressure, surface condition, heat/load path, HTC/CHF or other performance measures, calibration, sensors, sampling/frame rate, spatial scale, synchronization, uncertainty, and data-reduction equations.

Add mechanism-level dimensionless groups only when defined and useful. State equations, property-evaluation states, and validity. For legacy files, use parsers or feature extractors to recover headings, units, times, coordinates, instrument settings, and ontology matches, then verify extracted metadata.

Profile new data against neighboring datasets and physical laws without treating agreement as proof of quality. Preserve anomalous but credible data with flags and evidence rather than deleting them automatically.

## Public And Private Architecture

Keep protected inputs outside public packages. Publish code, schemas, public-data download scripts, authorized aggregates, synthetic demonstrations, and instructions for users to supply licensed inputs when appropriate.

Use GitHub or equivalent for code, manifests, documentation, and releases. Use a suitable archival or data platform for large data. Verify current limits, licenses, DOI support, versioning, and contribution workflow before choosing a platform.
