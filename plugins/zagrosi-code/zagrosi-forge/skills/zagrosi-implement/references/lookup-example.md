# Reusing catalog lookups within one order stream

An order export attaches a label to each product ID as the consumer requests
the next line. Duplicate IDs appear on separate lines. An empty label is valid.
An unknown ID raises `KeyError` when the consumer reaches it. Each export sees
one immutable catalog snapshot, and a lookup has no caller-visible side effect.

The existing loop loads a label for every line. If catalog reads dominate the
cost, reuse successful lookups for the lifetime of one stream. A global cache
could outlive the snapshot. Fetching every distinct ID up front would consume
the stream early and could raise before returning earlier valid lines.

```pycon
>>> def labeled_lines(product_ids, load_label):
...     labels = {}
...     for product_id in product_ids:
...         if product_id not in labels:
...             labels[product_id] = load_label(product_id)
...         yield product_id, labels[product_id]

```

Compare reads on the same input. The empty label catches implementations that
use truthiness to decide whether a label was cached.

```pycon
>>> catalog = {"A": "", "B": "Blue"}
>>> reads = []
>>> def load_label(product_id):
...     reads.append(product_id)
...     return catalog[product_id]
>>> order = ["A", "B", "A"]
>>> original = [(product_id, load_label(product_id)) for product_id in order]
>>> original, reads
([('A', ''), ('B', 'Blue'), ('A', '')], ['A', 'B', 'A'])
>>> reads.clear()
>>> list(labeled_lines(iter(order), load_label)) == original
True
>>> reads
['A', 'B']

```

Check a second export after the catalog changes. Only the requested prefix is
read. The missing ID raises after the first valid result.

```pycon
>>> catalog["A"] = "Amber"
>>> reads.clear()
>>> rows = labeled_lines(iter(["A", "missing", "B"]), load_label)
>>> next(rows)
('A', 'Amber')
>>> next(rows)
Traceback (most recent call last):
...
KeyError: 'missing'
>>> reads
['A', 'missing']

```

This change reduced catalog reads from three to two for the measured input.
It retains one entry per distinct product until the stream closes. If distinct
IDs can exhaust memory, establish a working-set bound or keep the original
streaming lookup. End-to-end latency depends on the real catalog and workload.

Run the example from the Forge repository root with
`python -m doctest skills/zagrosi-implement/references/lookup-example.md`.
