---
name: visual-storyboard-designer
description: Pick a FigureAtlas figure when a paper, slide, poster, or video frame needs a chart, diagram, map, or illustration. The catalog has 300 verified figure types across 15 families.
---

# FigureAtlas storyboard skill

Use this skill when an agent needs a figure for a paper, a slide, a poster, or a video frame.

## Selection order

1. Pick the output frame: journal single column, journal double column, 16:9 slide, 4:3 slide, A0 poster, or 1080p video.
2. Pick the family from the table below.
3. Pick one figure id from `CATALOG.md`. Do not invent a 301st type.

## Families

| Family | Use it when | Count |
|---|---|---:|
| Format adapters | The same figure must fit a journal column, a slide, or a poster | 18 |
| Distribution and comparison | Groups, ranks, or uncertainty are the point | 28 |
| Correlation and dimension reduction | Two or more measures move together | 20 |
| Time and process | The horizontal axis is time or sequence | 16 |
| Part-to-whole and sets | Shares, overlap, or hierarchy matter | 14 |
| Networks and systems | The slide explains components and flow | 25 |
| Mathematics and derivation | The lesson shows a geometric reason | 18 |
| Model structure and evaluation | The paper reports a model | 20 |
| Life science and omics | The figure is genomic, cellular, or phylogenetic | 37 |
| Chemistry and materials | The figure is a structure, spectrum, or process | 17 |
| Physics, engineering, and signals | The figure is a field, circuit, orbit, or waveform | 28 |
| Maps and space | Location is part of the claim | 16 |
| Scientific illustration | The reader needs a mechanism, not a statistic | 20 |
| Tables, code, and legends | The claim is a table, listing, or color key | 8 |
| Clinical and epidemiology | The paper follows a clinical reporting diagram | 15 |

## Call

```python
from figureatlas import render_figure
html = render_figure("161")  # volcano plot
```

Legacy specialized renderers such as `render_quantum_bloch_circuit` remain importable.
