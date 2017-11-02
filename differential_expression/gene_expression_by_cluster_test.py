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
            ["cell1", "Ttyh1", 3],
            ["cell2", "Ttyh1", 45],
            ["cell2", "Malat1", 10],
            ["cell3", "Ttyh1", 50],
            ["cell3", "mt-Rnr2", 10],
            ["cell4", "mt-Rnr2", 10]
        ]
    )

    cls.cluster_table_name = cls.client.path("cluster_assignments")
    cls.client.populate_table(
        cls.cluster_table_name,
        [("cell", "STRING"), ("cluster", "INTEGER")],
        [
            ["cell1", 1],
            ["cell2", 2],
            ["cell3", 2],
            ["cell4", 1]
        ]
    )

  def test_raw_data_counts(self):
    """Test bq.Client.get_query_results."""
    sql = Template(
        open("gene_expression_by_cluster.sql", "r").read()).render({
            "RAW_DATA_TABLE": self.src_table_name,
            "CLUSTER_TABLE": self.cluster_table_name,
            "MARKER_GENE_LIST": "'Ttyh1', 'Malat1'"
        })

    result = self.client.get_query_results(sql)

    self.assertSetEqual(
        set(result),
        set([("Ttyh1", 1, 3.0, 0.5),
             ("Ttyh1", 2, (45.0+50.0)/2.0, 1.0),
             ("Malat1", 2, 10.0, 0.5)]))

if __name__ == "__main__":
  unittest.main()
