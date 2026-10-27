---
name: histolab
description: Extracts tiles and preprocesses H&E whole slide images with the histolab Python library (OpenSlide), covering slide inspection, tissue masks (TissueMask, BiggestTissueBoxMask), RandomTiler, GridTiler and ScoreTiler extraction, image and morphological filters, and Macenko or Reinhard stain normalization. Use when building a tile dataset from WSI files for deep learning. Use when detecting tissue and excluding background or pen annotations. Use when previewing tile locations and exporting tile CSV reports. Use when normalizing stain variation across slides. Not for spatial proteomics, multiplexed imaging, or deep learning pipelines; use pathml for those.
license: Apache-2.0 license
compatibility: Requires Python 3.8–3.11 (histolab 0.7.0), OpenSlide system libraries, and Linux or macOS. Sample data via histolab.data requires pooch.
metadata:
  version: '1.3'
  category: clinical-and-health
  maintainer: Kalaris Labs
  tags: digital pathology, whole slide images, H&E, tile extraction, medical imaging
---

# Histolab

## Overview

Histolab is a Python library for processing whole slide images (WSI) in digital pathology. It automates tissue detection, extracts informative tiles from gigapixel images, and prepares datasets for deep learning pipelines. The library handles multiple WSI formats, implements sophisticated tissue segmentation, and provides flexible tile extraction strategies.

## Installation

Install OpenSlide system libraries first ([OpenSlide download](https://openslide.org/download/)), then install histolab:

```bash
uv pip install histolab
```

For built-in TCGA sample slides via `histolab.data`, also install pooch:

```bash
uv pip install pooch
```

Histolab 0.7.0 (latest stable) supports Python 3.8–3.11 on Linux and macOS. Windows is not supported as of 0.7.0.

## Quick Start

Basic workflow for extracting tiles from a whole slide image:

```python
from histolab.slide import Slide
from histolab.tiler import RandomTiler

# Load slide
slide = Slide("slide.svs", processed_path="output/")

# Configure tiler
tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=100,
    level=0,
    seed=42
)

# Preview tile locations
tiler.locate_tiles(slide, n_tiles=20)

# Extract tiles
tiler.extract(slide)
```

## Core Capabilities

Six capability areas, each with worked code, are documented in
[references/core_capabilities.md](references/core_capabilities.md):

1. **Slide management** — opening slides, properties, levels, thumbnails, and scaled images.
2. **Tissue detection and masks** — `TissueMask` and `BiggestTissueBoxMask`, and custom masks.
3. **Tile extraction** — random, grid, and score-based tilers with size, level, and
   tissue-fraction control.
4. **Filters and preprocessing** — image and morphological filters, and composing them.
5. **Stain normalization** — Reinhard and Macenko normalization against a target image.
6. **Visualization** — locating tiles on the slide and inspecting masks and extractions.

Five end-to-end workflows are in
[references/typical_workflows.md](references/typical_workflows.md). Per-topic detail lives
in [references/slide_management.md](references/slide_management.md),
[references/tissue_masks.md](references/tissue_masks.md),
[references/tile_extraction.md](references/tile_extraction.md),
[references/filters_preprocessing.md](references/filters_preprocessing.md), and
[references/visualization.md](references/visualization.md).

## Best Practices

### Slide Loading and Inspection
1. Always inspect slide properties before processing
2. Save thumbnails with `slide.thumbnail.save()` for quick visual review
3. Check pyramid levels and dimensions
4. Verify tissue is present using thumbnails

### Tissue Detection
1. Preview masks with `locate_mask()` before extraction
2. Use `TissueMask` for multiple sections, `BiggestTissueBoxMask` for single sections
3. Customize filters for specific stains (H&E vs IHC)
4. Handle pen annotations with custom masks
5. Test masks on diverse slides

### Tile Extraction
1. **Always preview with `locate_tiles()` before extracting**
2. Choose appropriate tiler:
   - RandomTiler: Sampling and exploration
   - GridTiler: Complete coverage
   - ScoreTiler: Quality-driven selection
3. Set appropriate `tissue_percent` threshold (70-90% typical)
4. Use seeds for reproducibility in RandomTiler
5. Extract at appropriate pyramid level for analysis resolution
6. Enable logging for large datasets

### Performance
1. Extract at lower levels (1, 2) for faster processing
2. Use `BiggestTissueBoxMask` over `TissueMask` when appropriate
3. Adjust `tissue_percent` to reduce invalid tile attempts
4. Limit `n_tiles` for initial exploration
5. Use `pixel_overlap=0` for non-overlapping grids

### Quality Control
1. Validate tile quality (check for blur, artifacts, focus)
2. Review score distributions for ScoreTiler
3. Inspect top and bottom scoring tiles
4. Monitor tissue coverage statistics
5. Filter extracted tiles by additional quality metrics if needed

## Common Use Cases

### Training Deep Learning Models
- Extract balanced datasets using RandomTiler across multiple slides
- Use ScoreTiler with NucleiScorer to focus on cell-rich regions
- Extract at consistent resolution (level 0 or level 1)
- Generate CSV reports for tracking tile metadata

### Whole Slide Analysis
- Use GridTiler for complete tissue coverage
- Extract at multiple pyramid levels for hierarchical analysis
- Maintain spatial relationships with grid positions
- Use `pixel_overlap` for sliding window approaches

### Tissue Characterization
- Sample diverse regions with RandomTiler
- Quantify tissue coverage with masks
- Extract stain-specific information with HED decomposition
- Compare tissue patterns across slides

### Quality Assessment
- Identify optimal focus regions with ScoreTiler
- Detect artifacts using custom masks and filters
- Assess staining quality across slide collection
- Flag problematic slides for manual review

### Dataset Curation
- Use ScoreTiler to prioritize informative tiles
- Filter tiles by tissue percentage
- Generate reports with tile scores and metadata
- Create stratified datasets across slides and tissue types

## Troubleshooting

### No tiles extracted
- Lower `tissue_percent` threshold
- Verify slide contains tissue (check thumbnail)
- Ensure extraction_mask captures tissue regions
- Check tile_size is appropriate for slide resolution

### Many background tiles
- Enable `check_tissue=True`
- Increase `tissue_percent` threshold
- Use appropriate mask (TissueMask vs BiggestTissueBoxMask)
- Customize mask filters to better detect tissue

### Extraction very slow
- Extract at lower pyramid level (level=1 or 2)
- Reduce `n_tiles` for RandomTiler/ScoreTiler
- Use RandomTiler instead of GridTiler for sampling
- Use BiggestTissueBoxMask instead of TissueMask

### Tiles have artifacts
- Implement custom annotation-exclusion masks
- Adjust filter parameters for artifact removal
- Increase small object removal threshold
- Apply post-extraction quality filtering

### Inconsistent results across slides
- Use same seed for RandomTiler
- Normalize staining with `MacenkoStainNormalizer` or `ReinhardStainNormalizer`
- Adjust `tissue_percent` per staining quality
- Implement slide-specific mask customization

## Resources

This skill includes detailed reference documentation in the `references/` directory:

### references/slide_management.md
Comprehensive guide to loading, inspecting, and working with whole slide images:
- Slide initialization and configuration
- Built-in sample datasets
- Slide properties and metadata
- Thumbnail generation and visualization
- Working with pyramid levels
- Multi-slide processing workflows
- Best practices and common patterns

### references/tissue_masks.md
Complete documentation on tissue detection and masking:
- TissueMask, BiggestTissueBoxMask, BinaryMask classes
- How tissue detection filters work
- Customizing masks with filter chains
- Visualizing masks
- Creating custom rectangular and annotation-exclusion masks
- Integration with tile extraction
- Best practices and troubleshooting

### references/tile_extraction.md
Detailed explanation of tile extraction strategies:
- RandomTiler, GridTiler, ScoreTiler comparison
- Available scorers (NucleiScorer, CellularityScorer, custom)
- Common and strategy-specific parameters
- Tile preview with locate_tiles()
- Extraction workflows and CSV reporting
- Advanced patterns (multi-level, hierarchical)
- Performance optimization
- Troubleshooting common issues

### references/filters_preprocessing.md
Complete filter reference and preprocessing guide:
- Image filters (color conversion, thresholding, contrast)
- Morphological filters (dilation, erosion, opening, closing)
- Filter composition and chaining
- Built-in stain normalization (Macenko, Reinhard) and filter-based alternatives
- Common preprocessing pipelines
- Applying filters to tiles
- Custom mask filters
- Quality control filters
- Best practices and troubleshooting

### references/visualization.md
Comprehensive visualization guide:
- Slide thumbnail display and saving
- Mask visualization techniques
- Tile location preview
- Displaying extracted tiles and creating mosaics
- Quality assessment visualizations
- Multi-slide comparison
- Filter effect visualization
- Exporting high-resolution figures and PDFs
- Interactive visualization in Jupyter notebooks

**Usage pattern:** Reference files contain in-depth information to support workflows described in this main skill document. Load specific reference files as needed for detailed implementation guidance, troubleshooting, or advanced features.

## Agent operating procedure

1. **Check the environment.** Confirm data access permissions, de-identification status and the governing regulations or protocols.
2. **Pin down the inputs.** Confirm formats, identifiers and parameters from the data or the user. Ask rather than guess any value that changes the result.
3. **Run a small version first.** Work on a de-identified sample or synthetic data first.
4. **Execute the full task** using the instructions and references above.
5. **Validate the result.** Check outputs against clinical guidelines and reporting standards; have a qualified human review clinical content.
6. **Report.** State what was run (versions, commands, parameters), what was checked, and what is still uncertain.

| If this happens | Do this |
|---|---|
| Data appears to contain identifiable patient information | Stop and ask the user before processing further. |
| A function, flag or endpoint in these instructions is missing in the installed version | Check the installed version's own documentation (`help()`, `--help`, official docs), adapt, and tell the user. Never invent an API. |
| A required input, identifier or parameter is ambiguous | Ask the user, or state the assumption explicitly before running. |

**Integrity rules**

- Never fabricate results, parameters, identifiers, citations or statistics. If something cannot be run or verified, say so plainly.
- Outputs are decision support for qualified professionals, not medical advice; never present them as diagnoses or orders.
- Treat version-specific details here as possibly outdated: confirm them against the official documentation for the installed version.
- Ask before actions that cost money, consume shared GPUs or cloud quota, touch personal or patient data, or cannot be undone.

## Related skills

- `pathml`: Covers local, research-only computational pathology with PathML 3.0.5: loading and tiling whole-slide images (OpenSlide, Bio-Formats), prep…
- `scientific-slides`: Build slide decks and presentations for research talks.
- `segment-anything-model`: Foundation model for image segmentation with zero-shot transfer.
