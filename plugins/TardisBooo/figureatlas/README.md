# FigureAtlas

**English** | [中文说明](README_ZH.md)

> **300 verified figure types for papers, slides, posters, and video frames.**

[![Figures](https://img.shields.io/badge/figures-300-blue.svg)](CATALOG.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Agent skill](https://img.shields.io/badge/Agent%20skill-ready-emerald.svg)](skills/visual-storyboard-designer/SKILL.md)

FigureAtlas is a figure catalog for people and coding agents. A paper, a slide, and a poster often need the same result in different frames. The catalog names the figure once. The frame is chosen separately.

The old project name was Scientific Visual Studio. The repository is now `figureatlas`, which is easier to say and easier to search.

中文说明在 [README_ZH.md](README_ZH.md)。同一份图鉴有 300 种已经过截图验证的图，分成 15 族。主页下面先放 30 张，完整图库在 [GALLERY.md](GALLERY.md)。

## What is in the box

- **300 figure types** across 15 families. The full index is [CATALOG.md](CATALOG.md).
- **A screenshot for every type.** Verification writes the PNG before the figure is added to the gallery. See [GALLERY.md](GALLERY.md).
- **26 specialized scientific renderers** from the previous release: Bloch sphere, Bode plot, sequence logo, reaction scheme, Feynman diagram, and the rest.
- **One call for the whole catalog.**

```python
from figureatlas import render_figure
html = render_figure("161")  # volcano plot
```

The DeepSeek Harness package declares `dsh.bundle` in `package.json` and registers the skill through `cordis.patch.yml`.

## Families

| Family | Figures | Start here |
|---|---:|---|
| Format adapters | 18 | Journal column, 16:9 slide, A0 poster |
| Distribution and comparison | 28 | Histogram, box plot, forest plot |
| Correlation and dimension reduction | 20 | Scatter, heatmap, PCA |
| Time and process | 16 | Line, Kaplan-Meier, Gantt |
| Part-to-whole and sets | 14 | Treemap, Venn, UpSet |
| Networks and systems | 25 | Sankey, sequence, C4 |
| Mathematics and derivation | 18 | Basis map, slope field, proof |
| Model structure and evaluation | 20 | Confusion matrix, SHAP, U-Net |
| Life science and omics | 37 | Volcano, Circos, UMAP |
| Chemistry and materials | 17 | Reaction scheme, NMR, unit cell |
| Physics, engineering, and signals | 28 | Bode, Smith chart, waveform |
| Maps and space | 16 | Choropleth, flow map, trajectory |
| Scientific illustration | 20 | Mechanism, apparatus, graphical abstract |
| Tables, code, and legends | 8 | Three-line table, code block |
| Clinical and epidemiology | 15 | CONSORT, swimmer, nomogram |

## Gallery

Thirty figures from the verified set. The other 270 are in [GALLERY.md](GALLERY.md). Each card links to the captured HTML.

| | |
|:---:|:---:|
| <div align="center"><b>001 Cinematic title cover</b><br/><a href="assets/gallery/atlas/001_hero-cover.html"><img src="assets/gallery/atlas/001_hero-cover.png" width="360" alt="Cinematic title cover"/></a><br/><sub>电影级封面</sub></div> | <div align="center"><b>011 A0 poster module</b><br/><a href="assets/gallery/atlas/011_poster-a0.html"><img src="assets/gallery/atlas/011_poster-a0.png" width="360" alt="A0 poster module"/></a><br/><sub>A0 海报模块</sub></div> |
| <div align="center"><b>022 Density curve</b><br/><a href="assets/gallery/atlas/022_density.html"><img src="assets/gallery/atlas/022_density.png" width="360" alt="Density curve"/></a><br/><sub>密度曲线</sub></div> | <div align="center"><b>032 Stacked bars</b><br/><a href="assets/gallery/atlas/032_stacked-bar.html"><img src="assets/gallery/atlas/032_stacked-bar.png" width="360" alt="Stacked bars"/></a><br/><sub>堆叠柱状图</sub></div> |
| <div align="center"><b>042 Forest plot</b><br/><a href="assets/gallery/atlas/042_forest.html"><img src="assets/gallery/atlas/042_forest.png" width="360" alt="Forest plot"/></a><br/><sub>森林图</sub></div> | <div align="center"><b>053 Clustered heatmap</b><br/><a href="assets/gallery/atlas/053_cluster-heat.html"><img src="assets/gallery/atlas/053_cluster-heat.png" width="360" alt="Clustered heatmap"/></a><br/><sub>聚类热图</sub></div> |
| <div align="center"><b>063 ROC curve</b><br/><a href="assets/gallery/atlas/063_roc.html"><img src="assets/gallery/atlas/063_roc.png" width="360" alt="ROC curve"/></a><br/><sub>ROC 曲线</sub></div> | <div align="center"><b>073 Sparkline row</b><br/><a href="assets/gallery/atlas/073_sparkline.html"><img src="assets/gallery/atlas/073_sparkline.png" width="360" alt="Sparkline row"/></a><br/><sub>火花线</sub></div> |
| <div align="center"><b>083 Pie chart</b><br/><a href="assets/gallery/atlas/083_pie.html"><img src="assets/gallery/atlas/083_pie.png" width="360" alt="Pie chart"/></a><br/><sub>饼图</sub></div> | <div align="center"><b>094 Euler diagram</b><br/><a href="assets/gallery/atlas/094_euler.html"><img src="assets/gallery/atlas/094_euler.png" width="360" alt="Euler diagram"/></a><br/><sub>欧拉图</sub></div> |
| <div align="center"><b>104 Adjacency matrix</b><br/><a href="assets/gallery/atlas/104_adj-matrix.html"><img src="assets/gallery/atlas/104_adj-matrix.png" width="360" alt="Adjacency matrix"/></a><br/><sub>邻接矩阵</sub></div> | <div align="center"><b>114 C4 component</b><br/><a href="assets/gallery/atlas/114_c4-component.html"><img src="assets/gallery/atlas/114_c4-component.png" width="360" alt="C4 component"/></a><br/><sub>C4 组件</sub></div> |
| <div align="center"><b>125 Complex plane</b><br/><a href="assets/gallery/atlas/125_complex-plane.html"><img src="assets/gallery/atlas/125_complex-plane.png" width="360" alt="Complex plane"/></a><br/><sub>复平面</sub></div> | <div align="center"><b>135 Convolution window</b><br/><a href="assets/gallery/atlas/135_convolution.html"><img src="assets/gallery/atlas/135_convolution.png" width="360" alt="Convolution window"/></a><br/><sub>卷积滑窗</sub></div> |
| <div align="center"><b>145 Learning curve</b><br/><a href="assets/gallery/atlas/145_learning-curve.html"><img src="assets/gallery/atlas/145_learning-curve.png" width="360" alt="Learning curve"/></a><br/><sub>学习曲线</sub></div> | <div align="center"><b>156 Token flow</b><br/><a href="assets/gallery/atlas/156_token-flow.html"><img src="assets/gallery/atlas/156_token-flow.png" width="360" alt="Token flow"/></a><br/><sub>词元流向</sub></div> |
| <div align="center"><b>166 Enrichment bars</b><br/><a href="assets/gallery/atlas/166_enrich-bar.html"><img src="assets/gallery/atlas/166_enrich-bar.png" width="360" alt="Enrichment bars"/></a><br/><sub>富集条形</sub></div> | <div align="center"><b>176 Single-cell UMAP</b><br/><a href="assets/gallery/atlas/176_sc-umap.html"><img src="assets/gallery/atlas/176_sc-umap.png" width="360" alt="Single-cell UMAP"/></a><br/><sub>单细胞 UMAP 分群</sub></div> |
| <div align="center"><b>187 PCoA / NMDS</b><br/><a href="assets/gallery/atlas/187_pcoa.html"><img src="assets/gallery/atlas/187_pcoa.png" width="360" alt="PCoA / NMDS"/></a><br/><sub>PCoA / NMDS</sub></div> | <div align="center"><b>197 Reaction scheme</b><br/><a href="assets/gallery/atlas/197_reaction-scheme.html"><img src="assets/gallery/atlas/197_reaction-scheme.png" width="360" alt="Reaction scheme"/></a><br/><sub>二维分子反应式</sub></div> |
| <div align="center"><b>207 Powder XRD</b><br/><a href="assets/gallery/atlas/207_xrd.html"><img src="assets/gallery/atlas/207_xrd.png" width="360" alt="Powder XRD"/></a><br/><sub>XRD</sub></div> | <div align="center"><b>218 Bode and Nyquist</b><br/><a href="assets/gallery/atlas/218_bode-nyquist.html"><img src="assets/gallery/atlas/218_bode-nyquist.png" width="360" alt="Bode and Nyquist"/></a><br/><sub>Bode / Nyquist</sub></div> |
| <div align="center"><b>228 Wavelet scalogram</b><br/><a href="assets/gallery/atlas/228_scalogram.html"><img src="assets/gallery/atlas/228_scalogram.png" width="360" alt="Wavelet scalogram"/></a><br/><sub>小波尺度图</sub></div> | <div align="center"><b>238 Rack elevation</b><br/><a href="assets/gallery/atlas/238_rack.html"><img src="assets/gallery/atlas/238_rack.png" width="360" alt="Rack elevation"/></a><br/><sub>机架图</sub></div> |
| <div align="center"><b>248 Isoline map</b><br/><a href="assets/gallery/atlas/248_iso-map.html"><img src="assets/gallery/atlas/248_iso-map.png" width="360" alt="Isoline map"/></a><br/><sub>等值线地图</sub></div> | <div align="center"><b>259 Code and memory inspector</b><br/><a href="assets/gallery/atlas/259_code-inspector.html"><img src="assets/gallery/atlas/259_code-inspector.png" width="360" alt="Code and memory inspector"/></a><br/><sub>源码与内存双栏</sub></div> |
| <div align="center"><b>269 Graphical abstract quad</b><br/><a href="assets/gallery/atlas/269_abstract-quad.html"><img src="assets/gallery/atlas/269_abstract-quad.png" width="360" alt="Graphical abstract quad"/></a><br/><sub>图形摘要四格</sub></div> | <div align="center"><b>279 Coefficient table</b><br/><a href="assets/gallery/atlas/279_coef-table.html"><img src="assets/gallery/atlas/279_coef-table.png" width="360" alt="Coefficient table"/></a><br/><sub>回归系数表</sub></div> |
| <div align="center"><b>290 Nomogram</b><br/><a href="assets/gallery/atlas/290_nomogram.html"><img src="assets/gallery/atlas/290_nomogram.png" width="360" alt="Nomogram"/></a><br/><sub>列线图</sub></div> | <div align="center"><b>300 Network meta-analysis league</b><br/><a href="assets/gallery/atlas/300_league-table.html"><img src="assets/gallery/atlas/300_league-table.png" width="360" alt="Network meta-analysis league"/></a><br/><sub>网状荟萃联赛表</sub></div> |

The full screenshot set lives in `assets/gallery/atlas/`. The copies used for the pass/fail check stay in `assets/gallery/_staging/`.

## License

[Apache 2.0](LICENSE).
