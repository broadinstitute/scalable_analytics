# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
"""Test encoding of sparse count data to TensorFlow features."""

import unittest
from trainer import preprocess_measurements as preproc

# Test data.
SAMPLE_ID = 'cell1'

MEASUREMENTS = [{
    preproc.SAMPLE_COLUMN: SAMPLE_ID,
    preproc.MEASUREMENT_COLUMN: 'Glul',
    preproc.VALUE_COLUMN: 8
}, {
    preproc.SAMPLE_COLUMN: SAMPLE_ID,
    preproc.MEASUREMENT_COLUMN: 'Prkca',
    preproc.VALUE_COLUMN: 35
}]


class PreprocessMeasurementsTest(unittest.TestCase):

  def test_sample_measurements_to_example(self):
    expected = """features {
  feature {
    key: "meas"
    value {
      bytes_list {
        value: "Glul"
        value: "Prkca"
      }
    }
  }
  feature {
    key: "sample_name"
    value {
      bytes_list {
        value: "cell1"
      }
    }
  }
  feature {
    key: "values"
    value {
      float_list {
        value: 8
        value: 35
      }
    }
  }
}
"""
    self.assertEqual(
        expected,
        str(preproc.sample_measurements_to_example(SAMPLE_ID, MEASUREMENTS)))


if __name__ == '__main__':
  unittest.main()
