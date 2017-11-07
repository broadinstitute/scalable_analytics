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
    # Use BigQuery for this test.
    super(QueryTest, cls).setUpClass(use_mocks=False)

  @classmethod
  def create_mock_tables(cls):
    """Create mock tables."""
    cls.src_table_name = cls.client.path("cluster_assignments")
    cls.client.populate_table(
        cls.src_table_name,
        [
          SchemaField("cell", "STRING"),
          SchemaField("cluster", "INTEGER")
          ],
        [
            ["cell1", 1],
            ["cell2", 2],
            ["cell3", 3],
            ["cell4", 2],
            ["cell5", 2]
        ]
    )

  def test_raw_data_counts(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("cluster_cell_counts.sql", "r").read()).render(
            {"CLUSTER_TABLE": self.src_table_name})

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([(1, 1), (2, 3), (3, 1)]))

if __name__ == "__main__":
  unittest.main()
