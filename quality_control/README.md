Quality Control
===============

Once the data has been loaded into BigQuery, we can perform some filtering to identify data of sufficient quality to be used in downstream analyses.

(1) Identify passing cells by running queries [cell_metrics.sql](./cell_metrics.sql) and [passing_cells.sql](./passing_cells.sql) and materializing the result to new BigQuery tables.

(2) Identify passing genes by running queries [gene_metrics.sql](./gene_metrics.sql) and [passing_genes.sql](./passing_genes.sql) and materializing the result to new BigQuery tables.

As an example, [QualityControl.Rmd](./QualityControl.Rmd) has been provided to show the process end-to-end, but these queries can also be run manually in the BigQuery Web UI, via the bq command line tool, etc...  Just edit anything you see in {{ JINJA MARKUP }} to be the actual tables you want to use.

## If you want to change or update this code

To run the BigQuery query integration tests:

* Install [the test
  framework](https://github.com/verilylifesciences/analysis-py-utils)
  via `pip install git+https://github.com/verilylifesciences/analysis-py-utils.git@v0.1.0`
* and then run the test like so `python cell_metrics_test.py`
