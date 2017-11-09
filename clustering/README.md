Cluster filtered data
=====================

TensorFlow currently has implementations of both K-Means and Gaussian Mixture
Model clustering. For more detail, see [![ML Toolkit Overview](http://img.youtube.com/vi/Tuv5QYKU-MM/0.jpg)](https://www.youtube.com/watch?v=Tuv5QYKU-MM)

## Getting Started

1. [Set up the Dataflow SDK for Python](https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python)
2. [Set up Cloud ML Engine](https://cloud.google.com/ml-engine/docs/quickstarts/command-line)

```bash
virtualenv --system-site-packages ~/virtualEnvs/tensorflow
source ~/virtualEnvs/tensorflow/bin/activate
pip install --upgrade pip jinja2 google-cloud-dataflow tensorflow
# Downgrade six per https://stackoverflow.com/a/46301373/4138705
pip install six==1.10.0 --ignore-installed
```

3. Set some environment variables to make copy/pasting commands a bit easier.

  * `PROJECT_ID=<YOUR_PROJECT>`
  * `BUCKET=gs://<YOUR_BUCKET>` this should be the **regional** bucket you
  created during Cloud ML Engine setup.

## Configuration

(1) Create a new file `query.sql` to contain a query similar to the following.
This query will be used to pull the desired input data from BigQuery.

  * Edit your query to use the fully qualified table
    names for the `RAW_DATA_TABLE` created during [data loading](../data_loading)
    and the `PASSING_GENES_TABLE` and `PASSING_CELLS_TABLE` created during
    [quality control](./quality_control).
  * If you wish to run clustering locally for testing purposes, be sure to add
    a `LIMIT 1000` or use a smaller cell and/or gene list to reduce the amount of data
    retrieved.
  * Do not edit the `{{ Jinja markup }}`. Those values will be replaced by the
    Beam pipeline.
    ```
    SELECT
      gene AS {{ MEASUREMENT_COLUMN }},
      cell AS {{ SAMPLE_COLUMN }},
      -- If few gene names correspond to multiple gene ids, collapse those
      -- transcript counts.
      SUM(trans_cnt) AS {{ VALUE_COLUMN }}
    FROM
      `RAW_DATA_TABLE`
    WHERE
      trans_cnt > 0
      AND gene IN (
      SELECT
        gene
      FROM
        `PASSING_GENES_TABLE`)
      AND cell IN (
      SELECT
        cell
      FROM
        `PASSING_CELLS_TABLE`)
    GROUP BY
      gene,
      cell
    ```

(2) [Export](https://cloud.google.com/bigquery/docs/exporting-data) the contents
of `PASSING_GENES_TABLE` as a CSV file. This is the "vocabulary file" containing
the names of all possible measurements to expect in the QC-ed data.

## (Optional) Local execution

### Preprocess the data
Preprocess a little bit of measurement data locally:

```bash
python -m trainer.preprocess_measurements \
  --setup_file ./setup.py \
  --output ./scrna-seq \
  --project ${PROJECT_ID} \
  --input ./PATH/TO/THE/query.sql
```

### Learn the clusters
Cluster a little bit of measurement data locally via TensorFlow:

```bash
EXAMPLES_SUBDIR=<the date-time subdirectory created during the data preprocess step>
python -m trainer.cluster_measurements \
    --input_file_pattern ./scrna-seq/${EXAMPLES_SUBDIR}/examples* \
    --output_path ./cluster-tiny-k-5 \
    --num_clusters 5 \
    --vocabulary_file ./PATH/TO/THE/vocabulary_file \
    --num_train_steps 1000
```

Cluster a little bit of measurement data locally via gcloud:

```bash
EXAMPLES_SUBDIR=<the date-time subdirectory created during the data preprocess step>
gcloud --project ${PROJECT_ID} ml-engine local train \
    --module-name trainer.cluster_measurements \
    --package-path trainer/ \
    -- \
    --input_file_pattern ./scrna-seq/${EXAMPLES_SUBDIR}/examples* \
    --output_path ./ml-engine-cluster-tiny-k-5 \
    --num_clusters 5 \
    --vocabulary_file ./PATH/TO/THE/vocabulary_file \
    --num_train_steps 1000
```

## Cloud Execution

### Preprocess the data

Preprocess the full set of QC-ed measurement data on cloud:

```bash
python -m trainer.preprocess_measurements \
    --setup_file ./setup.py \
    --output ${BUCKET}/scrna-seq \
    --project ${PROJECT_ID} \
    --input ./PATH/TO/THE/query.sql \
    --runner DataflowRunner
```

### Learn the clusters

Perform training on cloud:

```bash
EXAMPLES_SUBDIR=<the date-time subdirectory created during the data preprocess step>
gsutil cp ./PATH/TO/THE/vocabulary_file \
  ${BUCKET}/scrna-seq/${EXAMPLES_SUBDIR}/vocabulary_file

JOB_NAME=cluster_cosine_distance_k_30
gcloud --project ${PROJECT_ID} ml-engine jobs submit training ${JOB_NAME} \
    --module-name trainer.cluster_measurements \
    --package-path trainer/ \
    --runtime-version 1.2 \
    --config config.yaml \
    --job-dir ${BUCKET}/models/${JOB_NAME} \
    --region us-central1 \
    -- \
    --input_file_pattern ${BUCKET}/scrna-seq/${EXAMPLES_SUBDIR}/examples* \
    --output_path ${BUCKET}/models/${JOB_NAME} \
    --num_clusters 30 \
    --vocabulary_file ${BUCKET}/scrna-seq/${EXAMPLES_SUBDIR}/vocabulary_file \
    --use_cosine_distance \
    --num_train_steps 1000 \
    --batch_size 1000

```

## Tensorboard

To inspect the behavior of training, launch TensorBoard and point it at the
summary logs produced during training — both during and after execution.

```bash
tensorboard --port=8080 \
    --logdir ${BUCKET}/models/${JOB_NAME}
```

### Predict the clusters

Run a Beam pipeline to obtain the cluster assignments. Note that Cloud ML Engine
batch prediction cannot currently be used with K-Means because the estimator
does not allow an [instance
key](https://cloud.google.com/ml-engine/docs/concepts/prediction-overview#batch_prediction_input_data)
to be used.

``` bash
EXPORT_SUBDIR=<model subdirectory underneath 'export/Servo/'>
BIGQUERY_DATASET_NAME=<the dataset for writing prediction output>
python -m trainer.predict_clusters \
    --setup_file ./setup.py \
    --model ${BUCKET}/models/${JOB_NAME}/export/Servo/${EXPORT_SUBDIR} \
    --input ${BUCKET}/scrna-seq/${EXAMPLES_SUBDIR}/examples* \
    --output ${BIGQUERY_DATASET_NAME}.${JOB_NAME} \
    --temp_location ${BUCKET}/models/${JOB_NAME}/tmp/ \
    --project ${PROJECT_ID} \
    --disk_size_gb 50 \
    --worker_machine_type n1-standard-1 \
    --runner DataflowRunner
```

The above command uses a smaller amount of disk than the default and single
core instance types so that autoscaling can work in a fine-grained manner.
