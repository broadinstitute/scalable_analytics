Load Bipolar Cell 2016 single-cell RNAseq data
==============================================

The following steps will transfer the source data from
https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE81904
to Cloud Platform and load it into BigQuery. All of these steps occur in the
cloud instead of a local machine to reduce network data transfer time.

# Create and configure a Compute Engine instance.

1. Use the [Cloud Console](https://console.cloud.google.com) to create and start a Compute Engine instance. For more detailed instructions please see the [Compute Engine documentation](https://cloud.google.com/compute/docs/instances/create-start-instance). Ensure that the instance:
    * has at least 13 GB of memory
    * uses image `Container-Optimized OS - stable`
    * resides in the same region as the destination Cloud Storage bucket
    * has "Allow full access to all Cloud APIs" checked.
2. Use the Cloud Console to ssh to the new instance.
3. Obtain the code in this repository.
```
git clone https://github.com/broadinstitute/scalable_analytics.git
```

# Transfer the data to Google Cloud Platform.

1. Transfer the data from the [Gene Expression Omnibus](https://www.ncbi.nlm.nih.gov/geo/) (GEO) to your instance. This takes ~1 minute.
```
wget \
  'https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE81904&format=file&file=GSE81904%5Fbipolar%5Fdata%5FCell2016%2ERdata%2Egz' \
  -O GSE81904_bipolar_data_Cell2016.Rdata.gz
```
2. Decompress the data.
```
gunzip GSE81904_bipolar_data_Cell2016.Rdata.gz
```

# Reshape the data.

1. Run an R Docker container to convert the RData file to a CSV file. This takes ~25 minutes.
```
docker run --tty --interactive --volume "${HOME}":/var/tmp --workdir /var/tmp rocker/r-base
# Now we're in an R session.
load("GSE81904_bipolar_data_Cell2016.Rdata")
write.csv(bipolar_dge, "wide_format_GSE81904_bipolar_data_Cell2016.csv")
quit()
```
2. Run the [CoreOS toolbox](https://cloud.google.com/container-optimized-os/docs/how-to/toolbox) Docker container, which
has Python and gcloud preinstalled, to reshape the data to long format and perform a
[streaming upload to Cloud Storage](https://cloud.google.com/storage/docs/gsutil/commands/cp#streaming-transfers). This takes ~6 minutes.
```
/usr/bin/toolbox --bind=$HOME:/root
# Now we're in a bash session in the toolbox container.
cat wide_format_GSE81904_bipolar_data_Cell2016.csv \
  | python scalable_analytics/data_loading/dense_to_sparse.py \
  |  gsutil cp - gs://BUCKET-NAME/sparse_format_GSE81904_bipolar_data_Cell2016.csv
```

# Load the data into BigQuery.

1. Create a destination BigQuery dataset either via the [BigQuery Web UI](https://bigquery.cloud.google.com)
or via the [bq Command-Line Tool](https://cloud.google.com/bigquery/bq-command-line-tool).
```
# Still in the bash session in the toolbox container.
bq mk DATASET-NAME
```
2. Load the data. This takes ~2 minutes.
```
bq load --autodetect DATASET-NAME.TABLE-NAME \
  gs://BUCKET-NAME/sparse_format_GSE81904_bipolar_data_Cell2016.csv
```
