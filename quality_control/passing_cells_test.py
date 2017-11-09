# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
from jinja2 import Template
from google.cloud.bigquery.schema import SchemaField
from verily.bigquery_wrapper import bq_test_case


class QueryTest(bq_test_case.BQTestCase):

  @classmethod
  def setUpClass(cls):
    """Set up class."""
    # Use BigQuery for this test instead of the SQLite mock
    # because the query contains integers divided to yield a
    # float result which is not supported by SQLite.
    super(QueryTest, cls).setUpClass(use_mocks=False)

  @classmethod
  def create_mock_tables(cls):
    """Create mock tables."""
    cls.src_table_name = cls.client.path("cell_metrics")
    cls.client.populate_table(
        cls.src_table_name,
        [
          SchemaField("cell", "STRING"),
          SchemaField("alltrans", "INTEGER"),
          SchemaField("mttrans", "INTEGER"),
          SchemaField("gene_cnt", "INTEGER")
          ],
        [
            ["cell1_pass", 50, 4, 501],
            ["cell2_fail_too_few_genes", 50, 4, 500],
            ["cell3_fail_too_much_mt", 50, 5, 501],
            ["cell4_fail_both", 50, 5, 500]
        ]
    )

  def test_passing_cells(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("passing_cells.sql", "r").read()).render(
            {"CELL_METRICS_TABLE": self.src_table_name})

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([("cell1_pass",)]))

if __name__ == "__main__":
  unittest.main()
