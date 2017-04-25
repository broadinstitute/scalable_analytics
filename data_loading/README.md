Load Data
=========

Perform the following steps to load single-cell expression data into BigQuery.

## (1) Convert source data to long, sparse format.

For a CSV file in dense matrix format, such as:

```
,cell1,cell2,cell3
gene1,0.0,0.0,3.0
gene2,0.0,0.0,0.0
gene3,1.0,0.0,2.0
```

run [dense_to_long.py](./dense_to_long.py) to convert it to long, sparse format.  See the top of the script for instructions.

## (2) Load the reformatted data to BigQuery.

```
bq --project PROJECT load --autodetect DATASET_NAME.TABLE_NAME \
  gs://BUCKET-NAME/PATH/TO/LONG/SPARSE/FILE.csv
```