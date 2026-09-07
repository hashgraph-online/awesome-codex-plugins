# Dataset And Software Review Workflow

Use this reference when a review centers on datasets, software, model packages, benchmark suites, community databanks, or open research infrastructure.

## Define The Corpus

State the review purpose and inclusion boundary. Distinguish peer-reviewed papers, preprints, archival datasets, software repositories, model weights, benchmark suites, lab portals, standards, and educational examples.

Search across complementary channels:

- bibliographic databases and publisher sites;
- backward and forward citations from representative papers;
- author profiles, laboratory pages, and conference benchmark tracks;
- GitHub or other source-code hosts;
- Zenodo, Dryad, Dataverse, OSF, Mendeley Data, and institutional archives;
- Hugging Face or domain model/data hubs;
- user-provided BibTeX/Zotero libraries, slides, and local collections.

Record missed-paper diagnoses. Common causes include title/keyword mismatch, preprint-to-journal title changes, repository-first releases, dataset records without paper keywords, author-name variants, conference tracks, and searches limited to papers.

## Extract Comparable Fields

For each resource, record:

- stable identifier, version, access date, license, and maintenance state;
- physical system, geometry, fluid/material, operating range, and facility or simulation family;
- data modality, dimensions, temporal sampling, spatial scale, synchronization, and metadata;
- labels, preprocessing, split strategy, leakage controls, baseline tasks, metrics, and failure cases;
- code environment, pretrained weights, decoder/visualizer, examples, tests, and archival link;
- evidence maturity and limitations.

Use a taxonomy only when it helps readers make decisions. For multimodal thermal-fluid data, spatial-plus-temporal dimensionality can be one useful axis; do not force it onto unrelated reviews.

## Synthesize

Organize the review by mechanism, data modality, dimensionality, task, evidence maturity, benchmark readiness, or unresolved infrastructure gap. Avoid repository lists and one-resource-one-paragraph summaries.

Compare what resources enable:

- reproducible measurement or simulation;
- model training and fair comparison;
- cross-condition or cross-laboratory generalization;
- physical interpretation;
- reuse by a new user;
- community contribution and governance.

Balance author-generated resources with third-party work. Present laboratory resources as case studies or seed efforts within the field, and distinguish ownership and maintenance responsibility.

## Availability Statements

List author-generated data, software, and benchmark artifacts needed to reproduce or use the article. Mention third-party resources only when they are central to the reviewed infrastructure or required for reproduction, and label them explicitly as third-party resources.

Verify every URL, DOI, license, version, and repository state before finalizing. Do not imply that an archive, portal, or workbook is complete or fully open without checking dependencies and redistribution terms.
