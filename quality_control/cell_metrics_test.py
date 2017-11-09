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
    # because the query contains an IF which is not supported
    # by SQLite.
    super(QueryTest, cls).setUpClass(use_mocks=False)

  @classmethod
  def create_mock_tables(cls):
    """Create mock tables."""
    cls.src_table_name = cls.client.path("raw_data")
    cls.client.populate_table(
        cls.src_table_name,
        [
          SchemaField("cell", "STRING"),
          SchemaField("gene", "STRING"),
          SchemaField("trans_cnt", "INTEGER")
          ],
        [
            ["cell1", "Ttyh1", 0],
            ["cell2", "Ttyh1", 0],
            ["cell2", "Malat1", 10],
            ["cell3", "Ttyh1", 10],
            ["cell3", "mt-Rnr2", 10],
            ["cell4", "mt-Rnr2", 10]
        ]
    )

  def test_cell_metrics(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("cell_metrics.sql", "r").read()).render(
            {"RAW_DATA_TABLE": self.src_table_name})

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([
            ("cell2", 10, 0, 1),
            ("cell3", 20, 10, 2),
            ("cell4", 10, 10, 1)
        ]))

if __name__ == "__main__":
  unittest.main()
