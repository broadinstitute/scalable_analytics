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
    cls.src_table_name = cls.table_path("raw_data")
    cls.client.populate_table(
        cls.src_table_name,
        [("cell", "STRING"), ("gene", "STRING"), ("trans_cnt", "INTEGER")],
        [
            ["cell1", "Ttyh1", 0],
            ["cell2", "Ttyh1", 0],
            ["cell2", "Malat1", 10],
            ["cell3", "Ttyh1", 10],
            ["cell3", "mt-Rnr2", 10],
            ["cell4", "mt-Rnr2", 10]
        ]
    )

  def test_raw_data_counts(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("raw_data_counts.sql", "r").read()).render(
            {"RAW_DATA_TABLE": self.src_table_name})

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([(3, 4),]))

if __name__ == "__main__":
  unittest.main()
