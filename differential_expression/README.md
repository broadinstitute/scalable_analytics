Differential expression
=======================

After clustering has been performed, we can evaluate the clusters in a few different ways.

## Marker genes

Use [CompareClusters.Rmd](./CompareClusters.Rmd) to compute aggregate gene
expression per cluster using known marker genes and to render a dot plot.

Alternatively, query [gene_expression_by_cluster.sql](./gene_expression_by_cluster.sql)
can be run manually in the BigQuery Web UI, via the bq command line tool, etc...
Just edit anything you see in {{ JINJA MARKUP }} to be the actual tables or values
you want to use.

## Statistical tests

BigQuery supports a wide range of [functions and operators](https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-and-operators#offset-and-ordinal).  It also supports JavaScript [user-defined functions](https://cloud.google.com/bigquery/docs/reference/standard-sql/user-defined-functions).

[Testing_R_vs_JavaScript.Rmd](./Testing_R_vs_JavaScript.Rmd) demonstrates one way
to test mathematical results generated via BigQuery against those from an alternate
evironment such as R.

The specific example we demonstrate here is the differential expression implemented in https://github.com/broadinstitute/BipolarCell2016/blob/master/BCanalysis.pdf ported
to BigQuery.  To run it:

(1) Upload [binomial_distribution.js](./binomial_distribution.js) to a Google Cloud Storage bucket.

(2) Use [DifferentialExpression.Rmd](./CompareClusters.Rmd) to compute differential
expression of one particular cluster compared to all others.  It will materialize
the result of  [differential_expression_one_vs_the_rest.sql](./differential_expression_one_vs_the_rest.sql)
to a new table.

## If you want to change or update this code

To run the BigQuery query integration tests:

* Install [the test
  framework](https://github.com/verilylifesciences/analysis-py-utils)
  via `pip install git+https://github.com/verilylifesciences/analysis-py-utils.git@v0.1.0`
* and then run the test like so `python cell_metrics_test.py`
