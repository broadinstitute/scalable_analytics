# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
from jinja2 import Template
from verily.bigquery_wrapper import bq_test_case


class QueryTest(bq_test_case.BQTestCase):

  @classmethod
  def setUpClass(cls):
    """Set up class."""
    # Use BigQuery for this test.
    super(QueryTest, cls).setUpClass(use_mocks=False)

  @classmethod
  def create_mock_tables(cls):
    """Create mock tables."""
    cls.src_table_name = cls.client.path("raw_data")
    cls.client.populate_table(
        cls.src_table_name,
        [("cell", "STRING"), ("gene", "STRING"), ("trans_cnt", "INTEGER")],
        [
            ["cell1", "Ttyh1", 50],
            ["cell2", "Ttyh1", 45],
            ["cell2", "Malat1", 2],
            ["cell3", "Ttyh1", 50],
            ["cell4", "Ttyh1", 45],
            ["cell5", "Ttyh1", 50],
            ["cell6", "Ttyh1", 45],
            ["cell7", "Ttyh1", 50],
            ["cell8", "Ttyh1", 45],
            ["cell9", "Malat1", 20],
            ["cell10", "Malat1", 19],
            ["cell10", "Ttyh1", 1],
            ["cell11", "Malat1", 20],
            ["cell12", "Malat1", 19],
            ["cell13", "Malat1", 20],
            ["cell14", "Malat1", 19],
            ["cell15", "Malat1", 20],
            ["cell16", "Malat1", 19],
        ]
    )

    cls.cluster_table_name = cls.client.path("cluster_assignments")
    cls.client.populate_table(
        cls.cluster_table_name,
        [("cell", "STRING"), ("cluster", "INTEGER")],
        [
            ["cell1", 1],
            ["cell2", 1],
            ["cell3", 1],
            ["cell4", 1],
            ["cell5", 1],
            ["cell6", 1],
            ["cell7", 1],
            ["cell8", 1],
            ["cell9", 2],
            ["cell10", 2],
            ["cell11", 2],
            ["cell12", 2],
            ["cell13", 2],
            ["cell14", 2],
            ["cell15", 2],
            ["cell16", 2],
        ]
    )

    cls.cell_filter_table_name = cls.client.path("passing_cells")
    cls.client.populate_table(
        cls.cell_filter_table_name,
        [("cell", "STRING")],
        [
            ["cell1"],
            ["cell2"],
            ["cell3"],
            ["cell4"],
            ["cell5"],
            ["cell6"],
            ["cell7"],
            ["cell8"],
            ["cell9"],
            ["cell10"],
            ["cell11"],
            ["cell12"],
            ["cell13"],
            ["cell14"],
            ["cell15"],
            ["cell16"],
        ]
    )

    cls.gene_filter_table_name = cls.client.path("passing_genes")
    cls.client.populate_table(
        cls.gene_filter_table_name,
        [("gene", "STRING")],
        [
            ["Ttyh1"],
            ["Malat1"],
        ]
    )

  def test_raw_data_counts(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("differential_expression_one_vs_the_rest.sql", "r").read(
        )).render({
            "RAW_DATA_TABLE": self.src_table_name,
            "PASSING_CELLS_TABLE": self.cell_filter_table_name,
            "PASSING_GENES_TABLE": self.gene_filter_table_name,
            "CLUSTER_TABLE": self.cluster_table_name,
            "ONE_CLUSTER": 1,
            "EXTERNAL_JAVASCRIPT_LIBRARY": ""
        })

    # Replace reference to external JavaScript file with file contents.
    js = open("binomial_distribution.js", "r").read()
    sql = sql.replace("OPTIONS (\n  library=[\"\"]\n)", "")
    sql = sql.replace("return pbinom(k, n, p);",
                      js + "\nreturn pbinom(k, n, p);")

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([("Malat1", 5.960464477539063e-08, -2.0794415416798357,
              0.25, 19.5, 1),
             ("Ttyh1", 5.960464477539063e-08, 2.0794415416798357,
              47.5, 0.125, 1)]))

if __name__ == "__main__":
  unittest.main()
