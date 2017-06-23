# scalable_analytics

The code in this repository is designed for use with single-cell RNAseq data to help determine the cell types present in the dataset.

Perform the following four steps to obtain results:

1. [Load data](./data_loading)
2. [Perform quality control](./quality_control)
3. [Cluster filtered data](./clustering)
4. [Compute differential expresssion among the clusters](./differential_expression)

The analyses here are based on those in https://github.com/broadinstitute/BipolarCell2016
and https://github.com/broadinstitute/single_cell_analysis
ported to tools and techniques available (but not limited to) [Google Cloud Platform](https://cloud.google.com/).

* All steps occur in the cloud.
* Data loading makes use of [Docker](https://www.docker.com/), and [dsub](https://github.com/googlegenomics/dsub) via [Compute Engine](https://cloud.google.com/compute/docs/) for batch processing.
* The analyses make use of:
    * Standard SQL via [BigQuery](https://cloud.google.com/bigquery/docs/)
    * [Apache Beam](https://beam.apache.org/) via [Dataflow](https://cloud.google.com/dataflow/docs/)
    * [TensorFlow](https://www.tensorflow.org/) via [Cloud Machine Learning Engine](https://cloud.google.com/ml-engine/docs/)
* We suggest working through the introductory materials for each tool before working with the code in this repository.

