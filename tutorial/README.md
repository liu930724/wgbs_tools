# wgbstools tutorial
## Installation and configuration
First install `wgbstools` and configure the `hg19` genome
```bash
git clone https://github.com/nloyfer/wgbs_tools.git
cd wgbs_tools
python setup.py
wgbstools init_genome hg19
```

It is recommended to add wgbstools to your $PATH, E.g,
```bash
export PATH=${PATH}:$PWD
```

## All set. Let's begin
### Data and region
For this short tutorial, we will use the following publicly available samples from the [Roadmap Epigenomic Project](https://www.nature.com/articles/nature14248):

| SRX  | Tissue  |  Donor |
|---|---|---|
| SRX175350 |  Lung cells          | STL002
| SRX388743 |  Pancreas cells      | STL002
| SRX190161 |  Sigmoid colon cells | STL003

```bash
$ cd tutorial
$ ls -1 bams/*bam
Lung_STL002.small.bam
Pancreas_STL002.small.bam
Sigmoid_Colon_STL003.small.bam
```

To keep things compact, we consider a small region of ~4Kb, covering 100 CpG sites.
`convert` command translates genomic loci to CpG-index range and vice verca. It also prints genomic annotations, when available (currently only hg19).
```bash
$ region=chr3:119527929-119531943
$ wgbstools convert -r $region
chr3:119527929-119531943 - 4,015bp, 100CpGs: 5394767-5394867
intron  NR1I2
exon    NR1I2
intron  NR1I2
exon    NR1I2
```

### Generate pat & beta files
To generate [`pat`](docs/pat_format.md) and [`beta`](docs/beta_format.md)) files for each of the samples, we use the `bam2pat` command.
```bash
$ wgbstools bam2pat bams/*.bam -r $region
[wt bam2pat] bam: bams/Lung_STL002.small.bam
[ patter ] [ chr3 ] finished 2,793 lines. 1,813 good, 980 empty, 0 invalid. (success 100%)
[wt bam2pat] bgzipping and indexing:
[wt bam2pat] generated ./Lung_STL002.small.pat.gz
[wt bam2pat] generated ./Lung_STL002.small.beta
[wt bam2pat] bam: bams/Pancreas_STL002.small.bam
[ patter ] [ chr3 ] finished 814 lines. 516 good, 298 empty, 0 invalid. (success 100%)
[wt bam2pat] bgzipping and indexing:
[wt bam2pat] generated ./Pancreas_STL002.small.pat.gz
[wt bam2pat] generated ./Pancreas_STL002.small.beta
[wt bam2pat] bam: bams/Sigmoid_Colon_STL003.small.bam
[ patter ] [ chr3 ] finished 2,986 lines. 1,989 good, 997 empty, 0 invalid. (success 100%)
[wt bam2pat] bgzipping and indexing:
[wt bam2pat] generated ./Sigmoid_Colon_STL003.small.pat.gz
[wt bam2pat] generated ./Sigmoid_Colon_STL003.small.beta

$ ls -1 *pat* *beta
Lung_STL002.small.beta
Lung_STL002.small.pat.gz
Lung_STL002.small.pat.gz.csi
Pancreas_STL002.small.beta
Pancreas_STL002.small.pat.gz
Pancreas_STL002.small.pat.gz.csi
Sigmoid_Colon_STL003.small.beta
Sigmoid_Colon_STL003.small.pat.gz
Sigmoid_Colon_STL003.small.pat.gz.csi
```

### Segmentation 
Segment the region into homogenously methylated blocks
```bash
$ wgbstools segment --betas *beta --min_cpg 3 --max_bp 2000 -r $region -o blocks.small.bed
[wt segment] found 9 blocks
             (dropped 8 short blocks)
$ cat blocks.small.bed
chr3    119527929       119528187       5394767 5394772
chr3    119528217       119528243       5394774 5394777
chr3    119528246       119528309       5394777 5394781
chr3    119528384       119528418       5394782 5394786
chr3    119528430       119528783       5394786 5394796
chr3    119528806       119529245       5394796 5394834
chr3    119529584       119530116       5394837 5394844
chr3    119530396       119530598       5394846 5394856
chr3    119531385       119531943       5394858 5394867
```
The output bed file has 5 columns: chr, start, end, startCpG, endCpG (non inclusive). For example, the first block is chr3:119,527,929-119,528,187, 258bp, 5 CpG sites.
The segmentation algorithm finds a partition of the genome that optimizes some homogeneity score, i.e, the CpG sites in each block tend to have a similar methylation status. Many of the blocks are typically singletons (covering a single CpG site), but they are dropped when the `--min_cpg MIN_CPG` flag is specified.
In this example, the `segment` command segmented the region chr3:119,527,929-119,531,943 to 17 blocks, 9 of them cover at least 3 CpG sites.

####3 Index bed
Optional: bgzip and index the output blocks, make it easier to access.
`index` command wraps bgzip and tabix. It compresses a bed (or pat) file and generates corresponding index file. This step is necessary if you wish to visualize these blocks later using `vis` command.
```bash
$ wgbstools index blocks.small.bed
$ ls -1 blocks.small.*
blocks.small.bed.gz
blocks.small.bed.gz.tbi
```

### collapse beta files to blocks
Collapse the beta files to the blocks we just found:
```bash
$ wgbstools beta_to_table blocks.small.bed.gz --betas *beta
```

### Visualizations
try different forms of visualizations
```bash
$ wgbstools vis -r chr3:119527929-119531943 -b blocks.small.bed.gz *beta
$ wgbstools vis -r chr3:119527929-119531943 -b blocks.small.bed.gz *beta --heatmap
$ wgbstools vis -r chr3:119528585-119528783 -b blocks.small.bed.gz Sigmoid_Colon_STL003.small.pat.gz --min_len 4
$ wgbstools vis -r chr3:119528585-119528783 -b blocks.small.bed.gz Sigmoid_Colon_STL003.small.pat.gz --min_len 4 --strict
$ wgbstools view -s 5394796-5394834 Sigmoid_Colon_STL003.small.pat.gz --sub_sample .05
```