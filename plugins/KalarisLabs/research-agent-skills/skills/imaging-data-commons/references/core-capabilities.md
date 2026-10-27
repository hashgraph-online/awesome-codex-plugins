# Core Capabilities

The patterns below are the ones that go wrong when recalled from memory rather than checked.
Worked examples for each area live in the reference guides named inline.

### 1. Discovery — enumerate values before filtering on them

Filtering on a guessed `Modality` or `BodyPartExamined` string is the most common cause of an
empty result set. Enumerate first:

```python
modalities = client.sql_query("""
    SELECT DISTINCT Modality, COUNT(*) as series_count
    FROM index
    GROUP BY Modality
    ORDER BY series_count DESC
""")
print(modalities)
```

The same pattern works for any filter column, optionally narrowed by another —
`BodyPartExamined` within a `Modality`, `Manufacturer`, `collection_id`. On the REST path this
grounding is a single call — `GET /attributes/{attr}/values` returns values with counts — and the
cohort endpoints report a miscased value in `warnings` rather than as an empty result.

Two indices carry curated collection-level metadata the primary `index` does not, both
requiring `client.fetch_index(...)` first: `collections_index` (cancer types, tumor locations,
species, subject counts) and `analysis_results_index` (derived datasets — AI segmentations,
expert annotations, radiomics — with their source collections and modalities).

**Cancer type lives in `collections_index.cancer_types`, not in `index`** — filtering by
cancer type requires a join:

```python
client.fetch_index("collections_index")
results = client.sql_query("""
    SELECT i.collection_id, i.PatientID, i.SeriesInstanceUID, i.Modality
    FROM index i
    JOIN collections_index c ON i.collection_id = c.collection_id
    WHERE c.cancer_types LIKE '%Breast%'
      AND i.Modality = 'MR'
    LIMIT 20
""")
```

`client.sql_query()` returns a pandas DataFrame. Confirm column names with
`client.get_index_schema('index')` or `client.indices_overview` before writing a query rather
than assuming them.

See `references/sql_patterns.md` for filter-value discovery, annotation and segmentation
queries, size estimation, clinical linking, and version tracking ("what's new in vX" — use
`series_init_idc_version` / `series_revised_idc_version` in `index`, never
`prior_versions_index`).

### 2. Downloading DICOM files

**The two download methods take their first two arguments in opposite order.** This is the
most common source of broken IDC code — check it rather than recalling it:

| Method | First arg | Second arg | Use when |
|--------|-----------|------------|----------|
| `download_from_selection` | `downloadDir` (required) | filter kwargs (optional) | Filtering by collection, patient, study, or series |
| `download_dicom_series` | `seriesInstanceUID` (required) | `downloadDir` (required) | Downloading specific series by UID only |

**`download_from_selection` takes filter keyword arguments, NOT a DataFrame.** The name
"from_selection" refers to filtering the IDC index by criteria — not to accepting a pandas
DataFrame. To download query results, extract the UIDs into a list first:

```python
# Step 1: Query for series UIDs
series_df = client.sql_query("""
    SELECT SeriesInstanceUID
    FROM index
    WHERE Modality = 'CT'
      AND BodyPartExamined = 'CHEST'
      AND collection_id = 'nlst'
    LIMIT 5
""")

# Step 2: Extract UIDs as a list from the DataFrame
uids = list(series_df['SeriesInstanceUID'].values)

# Step 3: Pass the list to download_from_selection (NOT the DataFrame itself)
client.download_from_selection(
    downloadDir="./data/lung_ct",
    seriesInstanceUID=uids       # list of strings, not a DataFrame
)

# Alternative: download_dicom_series has seriesInstanceUID as FIRST arg (different order!)
client.download_dicom_series(
    seriesInstanceUID=uids,      # FIRST arg here
    downloadDir="./data/lung_ct"
)

# Whole collection: downloadDir is still the FIRST positional argument
client.download_from_selection(downloadDir="./data/rider", collection_id="rider_pilot")
```

Both methods default to AWS; pass `source_bucket_location="gcs"` to pull from Google Storage.

**Downloaded files are named `<crdc_instance_uuid>.dcm`, not by SOPInstanceUID.** The DICOM
UIDs are preserved inside the file metadata, not in the filename. Use the `crdc_instance_uuid`
column to map files back to the series they came from.

`idc download <collection|series-uid|manifest> --download-dir ./data` does the same from a
shell. See `references/cli_guide.md` for the `dirTemplate` hierarchy options (Python default:
`%collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID`; `dirTemplate=""`
flattens), manifest downloads with resume, and dry-run size estimation.

### 3. Visualizing IDC images

```python
viewer_url = client.get_viewer_URL(seriesInstanceUID=uid)        # one series
viewer_url = client.get_viewer_URL(studyInstanceUID=study_uid)   # all series in a study
```

Returns a browser URL — nothing is downloaded. The method selects OHIF v3 for radiology or
SLIM for slide microscopy automatically. Viewing by study is useful when a single DICOM Study
holds several Series (T1, T2, and DWI from one MRI session).

### 4. Licenses and citations — obligations, not optional steps

IDC data carries license terms and attribution requirements that follow it into any downstream
publication or product, and neither is inferable from the pixel data. **Check the license
before use, and generate citations for whatever you download.**

```python
# License breakdown for a selection
licenses = client.sql_query("""
    SELECT DISTINCT collection_id, license_short_name,
           COUNT(DISTINCT SeriesInstanceUID) as series_count
    FROM index GROUP BY collection_id, license_short_name
""")

# Citations for the same selection you downloaded (APA by default)
for citation in client.citations_from_selection(collection_id="rider_pilot"):
    print(citation)
```

About 97% of IDC data is CC BY (commercial use allowed with attribution) and about 3% is
CC BY-NC (non-commercial only). **Licenses attach to series, not collections** — 39 of 176
collections carry more than one — so check the selection you actually intend to use, and note
that the most restrictive term governs a mixed cohort.

Both tasks are available from all three access paths, so stay on whichever one the session is
already using: `idc-index` as above, `POST /v3/licenses` and `POST /v3/citations` over REST,
or the `get_licenses` and `get_citations` MCP tools. See
`references/licensing_and_citation.md` for the full license inventory, all three routes, the
citation formats (APA, BibTeX, CSL JSON, RDF Turtle), and what to include when publishing.

### 5. Reaching past the index

Pick the access path with the routing gate in *Overview*; *Data Access Options* above is the
full routing table.

Before reaching for BigQuery (which needs a billing-enabled GCP account), check whether a
specialized index table already has the column you want: search `client.indices_overview`,
then `client.fetch_index(...)` and query locally for free. BigQuery is required only for
private DICOM elements, per-segment anatomy (`segmentations`), and pre-extracted SR
measurements (`quantitative_measurements`, `qualitative_measurements`) — these have no
idc-index equivalent.
