Load Data
=========

Single-cell RNAseq data is sparse and the code in this section loads this data into a ["Tidy Data"](https://en.wikipedia.org/wiki/Tidy_data) table schema with (at a minimum) columns for cell identifier, gene name, and transcript count.

The general steps in this process are:

1. Convert source data to long, sparse format.

 * For example given a CSV file in dense matrix format, such as:
```
,cell1,cell2,cell3
gene1,0.0,0.0,3.0
gene2,0.0,0.0,0.0
gene3,1.0,0.0,2.0
```
 * reshape it as a tidy data CSV.
```
cell,gene,trans_cnt
cell1,gene3,1.0
cell3,gene1,3.0
cell3,gene3,2.0
```
2. Load the reshaped data to BigQuery.
```
bq --project PROJECT-ID load --autodetect DATASET-NAME.TABLE-NAME \
  gs://BUCKET-NAME/PATH/TO/LONG/SPARSE/FILE.csv
```

Here are instructions to load specific datasets, each demonstrating a different technique:

* [Bipolar Cell 2016](./BipolarCell2016.md) - uses a Compute Engine instance with the [Container-Optimized OS](https://cloud.google.com/container-optimized-os/docs/) VM image to run [Dockerized R](https://github.com/rocker-org/rocker)
* [10X Genomics 1.3 Million Brain Cells from E18 Mice](./10X_1.3_Million_Brain_Cells_from_E18_Mice.md) - uses a Compute Engine instance with the default VM image to run a Python script
* [10X Genomics 1.3 Million Brain Cells from E18 Mice - faster via parallel execution](./10X_1.3_Million_Brain_Cells_from_E18_Mice_parallel.md) - uses [Cloud Shell](https://github.com/googlegenomics/dsub) with [dsub](https://github.com/googlegenomics/dsub) for batch computing
