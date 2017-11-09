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
    super(QueryTest, cls).setUpClass(use_mocks=False)

  @classmethod
  def create_mock_tables(cls):
    """Create mock tables."""
    cls.src_table_name = cls.client.path("gene_metrics")

    cls.client.populate_table(
        cls.src_table_name,
        [
          SchemaField("gene", "STRING"),
          SchemaField("alltrans", "INTEGER"),
          SchemaField("cell_cnt", "INTEGER")
          ],
        [
            ["gene1_pass", 61, 31],
            ["gene2_fail_too_few_cells", 61, 30],
            ["gene3_fail_too_few_trans", 60, 31],
            ["gene4_fail_both", 60, 30]
        ]
    )

  def test_passing_genes(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("passing_genes.sql", "r").read()).render(
            {"GENE_METRICS_TABLE": self.src_table_name})

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([("gene1_pass",)]))

if __name__ == "__main__":
  unittest.main()
