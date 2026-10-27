# Histolab Core Capabilities

Slide management, tissue detection and masks, tile extraction, filters and preprocessing,
stain normalization, and visualization, each with worked code.

## Core Capabilities

### 1. Slide Management

Load, inspect, and work with whole slide images in various formats.

**Common operations:**
- Loading WSI files (SVS, TIFF, NDPI, etc.)
- Accessing slide metadata (dimensions, magnification, properties)
- Generating thumbnails for visualization
- Working with pyramidal image structures
- Extracting regions at specific coordinates

**Key classes:** `Slide`

**Reference:** `references/slide_management.md` contains comprehensive documentation on:
- Slide initialization and configuration
- Built-in sample datasets (prostate, ovarian, breast, heart, kidney tissues)
- Accessing slide properties and metadata
- Thumbnail generation and visualization
- Working with pyramid levels
- Multi-slide processing workflows

**Example workflow:**
```python
from histolab.slide import Slide
from histolab.data import prostate_tissue

# Load sample data
prostate_svs, prostate_path = prostate_tissue()

# Initialize slide
slide = Slide(prostate_path, processed_path="output/")

# Inspect properties
print(f"Dimensions: {slide.dimensions}")
print(f"Levels: {slide.levels}")
print(f"Magnification: {slide.properties.get('openslide.objective-power')}")

# Save thumbnail to processed_path
from pathlib import Path
Path(slide.processed_path).mkdir(parents=True, exist_ok=True)
slide.thumbnail.save(Path(slide.processed_path) / f"{slide.name}_thumbnail.png")
```

### 2. Tissue Detection and Masks

Automatically identify tissue regions and filter background/artifacts.

**Common operations:**
- Creating binary tissue masks
- Detecting largest tissue region
- Excluding background and artifacts
- Custom tissue segmentation
- Removing pen annotations

**Key classes:** `TissueMask`, `BiggestTissueBoxMask`, `BinaryMask`

**Reference:** `references/tissue_masks.md` contains comprehensive documentation on:
- TissueMask: Segments all tissue regions using automated filters
- BiggestTissueBoxMask: Returns bounding box of largest tissue region (default)
- BinaryMask: Base class for custom mask implementations
- Visualizing masks with `locate_mask()`
- Creating custom rectangular and annotation-exclusion masks
- Mask integration with tile extraction
- Best practices and troubleshooting

**Example workflow:**
```python
from histolab.masks import TissueMask, BiggestTissueBoxMask

# Create tissue mask for all tissue regions
tissue_mask = TissueMask()

# Visualize mask on slide
slide.locate_mask(tissue_mask)

# Get mask array
mask_array = tissue_mask(slide)

# Use largest tissue region (default for most extractors)
biggest_mask = BiggestTissueBoxMask()
```

**When to use each mask:**
- `TissueMask`: Multiple tissue sections, comprehensive analysis
- `BiggestTissueBoxMask`: Single main tissue section, exclude artifacts (default)
- Custom `BinaryMask`: Specific ROI, exclude annotations, custom segmentation

### 3. Tile Extraction

Extract smaller regions from large WSI using different strategies.

**Three extraction strategies:**

**RandomTiler:** Extract fixed number of randomly positioned tiles
- Best for: Sampling diverse regions, exploratory analysis, training data
- Key parameters: `n_tiles`, `seed` for reproducibility

**GridTiler:** Systematically extract tiles across tissue in grid pattern
- Best for: Complete coverage, spatial analysis, reconstruction
- Key parameters: `pixel_overlap` for sliding windows

**ScoreTiler:** Extract top-ranked tiles based on scoring functions
- Best for: Most informative regions, quality-driven selection
- Key parameters: `scorer` (NucleiScorer, CellularityScorer, custom)

**Common parameters:**
- `tile_size`: Tile dimensions (e.g., (512, 512))
- `level`: Pyramid level for extraction (0 = highest resolution)
- `check_tissue`: Filter tiles by tissue content
- `tissue_percent`: Minimum tissue coverage (default 80%)
- `extraction_mask`: Mask defining extraction region

**Reference:** `references/tile_extraction.md` contains comprehensive documentation on:
- Detailed explanation of each tiler strategy
- Available scorers (NucleiScorer, CellularityScorer, custom)
- Tile preview with `locate_tiles()`
- Extraction workflows and reporting
- Advanced patterns (multi-level, hierarchical extraction)
- Performance optimization and troubleshooting

**Example workflows:**

```python
from histolab.tiler import RandomTiler, GridTiler, ScoreTiler
from histolab.scorer import NucleiScorer

# Random sampling (fast, diverse)
random_tiler = RandomTiler(
    tile_size=(512, 512),
    n_tiles=100,
    level=0,
    seed=42,
    check_tissue=True,
    tissue_percent=80.0
)
random_tiler.extract(slide)

# Grid coverage (comprehensive)
grid_tiler = GridTiler(
    tile_size=(512, 512),
    level=0,
    pixel_overlap=0,
    check_tissue=True
)
grid_tiler.extract(slide)

# Score-based selection (most informative)
score_tiler = ScoreTiler(
    tile_size=(512, 512),
    n_tiles=50,
    scorer=NucleiScorer(),
    level=0
)
score_tiler.extract(slide, report_path="tiles_report.csv")
```

**Always preview before extracting:**
```python
# Preview tile locations on thumbnail
tiler.locate_tiles(slide, n_tiles=20)
```

### 4. Filters and Preprocessing

Apply image processing filters for tissue detection, quality control, and preprocessing.

**Filter categories:**

**Image Filters:** Color space conversions, thresholding, contrast enhancement
- `RgbToGrayscale`, `RgbToHsv`, `RgbToHed`
- `OtsuThreshold`, `AdaptiveThreshold`
- `StretchContrast`, `HistogramEqualization`

**Morphological Filters:** Structural operations on binary images
- `BinaryDilation`, `BinaryErosion`
- `BinaryOpening`, `BinaryClosing`
- `RemoveSmallObjects`, `RemoveSmallHoles`

**Composition:** Chain multiple filters together
- `Compose`: Create filter pipelines

**Reference:** `references/filters_preprocessing.md` contains comprehensive documentation on:
- Detailed explanation of each filter type
- Filter composition and chaining
- Common preprocessing pipelines (tissue detection, pen removal, nuclei enhancement)
- Applying filters to tiles
- Custom mask filters
- Quality control filters (blur detection, tissue coverage)
- Best practices and troubleshooting

**Example workflows:**

```python
from histolab.filters.compositions import Compose
from histolab.filters.image_filters import RgbToGrayscale, OtsuThreshold
from histolab.filters.morphological_filters import (
    BinaryDilation, RemoveSmallHoles, RemoveSmallObjects
)

# Standard tissue detection pipeline
tissue_detection = Compose([
    RgbToGrayscale(),
    OtsuThreshold(),
    BinaryDilation(disk_size=5),
    RemoveSmallHoles(area_threshold=1000),
    RemoveSmallObjects(area_threshold=500)
])

# Use with custom mask
from histolab.masks import TissueMask
custom_mask = TissueMask(filters=tissue_detection)

# Apply filters to tile
from histolab.tile import Tile
filtered_tile = tile.apply_filters(tissue_detection)
```

### 5. Stain Normalization

Standardize staining appearance across slides for deep learning (added in histolab 0.6.0).

**Key classes:** `MacenkoStainNormalizer`, `ReinhardStainNormalizer`

```python
from histolab.stain_normalizer import MacenkoStainNormalizer, ReinhardStainNormalizer
from PIL import Image

target = Image.open("reference_stain.png")  # Style reference slide/tile
source = Image.open("slide_to_normalize.png")

normalizer = MacenkoStainNormalizer()
normalizer.fit(target)
normalized = normalizer.transform(source)
normalized.save("normalized.png")
```

Use `ReinhardStainNormalizer()` for Reinhard color transfer. Fit on a representative target image, then transform source tiles or thumbnails. See `references/filters_preprocessing.md` for filter-based alternatives.

### 6. Visualization

Visualize slides, masks, tile locations, and extraction quality.

**Common visualization tasks:**
- Displaying slide thumbnails
- Visualizing tissue masks
- Previewing tile locations
- Assessing tile quality
- Creating reports and figures

**Reference:** `references/visualization.md` contains comprehensive documentation on:
- Slide thumbnail display and saving
- Mask visualization with `locate_mask()`
- Tile location preview with `locate_tiles()`
- Displaying extracted tiles and mosaics
- Quality assessment (score distributions, top vs bottom tiles)
- Multi-slide visualization
- Filter effect visualization
- Exporting high-resolution figures and PDF reports
- Interactive visualization in Jupyter notebooks

**Example workflows:**

```python
import matplotlib.pyplot as plt
from histolab.masks import TissueMask

# Display slide thumbnail
plt.figure(figsize=(10, 10))
plt.imshow(slide.thumbnail)
plt.title(f"Slide: {slide.name}")
plt.axis('off')
plt.show()

# Visualize tissue mask
tissue_mask = TissueMask()
slide.locate_mask(tissue_mask)

# Preview tile locations
tiler = RandomTiler(tile_size=(512, 512), n_tiles=50)
tiler.locate_tiles(slide, n_tiles=20)

# Display extracted tiles in grid
from pathlib import Path
from PIL import Image

tile_paths = list(Path("output/tiles/").glob("*.png"))[:16]
fig, axes = plt.subplots(4, 4, figsize=(12, 12))
axes = axes.ravel()

for idx, tile_path in enumerate(tile_paths):
    tile_img = Image.open(tile_path)
    axes[idx].imshow(tile_img)
    axes[idx].set_title(tile_path.stem, fontsize=8)
    axes[idx].axis('off')

plt.tight_layout()
plt.show()
```
