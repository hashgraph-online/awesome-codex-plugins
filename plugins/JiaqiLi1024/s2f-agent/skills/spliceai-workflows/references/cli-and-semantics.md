# SpliceAI CLI and Semantics

Source: `Readme/SpliceAI-master/README.md` and `setup.py` (package 1.3.1).

## Installation and entry point

The package exposes `spliceai=spliceai.__main__:main`. The documented installation is `pip install spliceai` or `conda install -c bioconda spliceai`; a source checkout can be installed with `python setup.py install`. The package lists Keras, pyfaidx, pysam, NumPy, and pandas; TensorFlow is installed separately, with `tensorflow` or `tensorflow-gpu` extras.

## VCF command

```bash
spliceai -I input.vcf -O output.vcf -R genome.fa -A grch37
```

`-A` accepts `grch37`, `grch38`, or a custom annotation file. `-D` is the maximum distance for gained/lost sites and defaults to 50. `-M 1` masks annotated acceptor/donor gains and unannotated acceptor/donor losses; raw `-M 0` is the default. Piped VCF is also supported: `cat input.vcf | spliceai -R genome.fa -A grch38 > output.vcf`.

The INFO payload is `ALLELE|SYMBOL|DS_AG|DS_AL|DS_DG|DS_DL|DP_AG|DP_AL|DP_DG|DP_DL`. DS fields are delta scores for acceptor/donor gain/loss; DP fields are relative delta positions. The maximum DS is interpreted as splice-altering probability, with paper cutoffs 0.2 (high recall), 0.5 (recommended), and 0.8 (high precision).

## Skip conditions

The upstream code only annotates variants inside genes and supports SNVs/simple indels where REF or ALT is one base. It skips variants close to chromosome ends (5 kb), deletions longer than twice `-D`, and variants inconsistent with the reference FASTA. A variant can have separate predictions for multiple genes.

## Custom sequence

The README loads `models/spliceai1.h5` through `spliceai5.h5`, one-hot encodes `N`-padded sequence with `context = 10000`, predicts with all five Keras models, and averages the predictions. `y[0,:,1]` is acceptor probability and `y[0,:,2]` is donor probability. This path has no VCF INFO annotation and does not infer a gene symbol.

