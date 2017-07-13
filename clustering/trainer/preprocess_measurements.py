# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
"""Convert sparse measurements data from BigQuery to tf.Example protos."""

import datetime
import logging
import os

import apache_beam as beam
from apache_beam.io.filesystem import CompressionTypes
from apache_beam.io import tfrecordio
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import WorkerOptions
from jinja2 import Template

import tensorflow as tf

from trainer.shared_constants import *


# Decouple source table column names from the dictionary keys used
# in this code.
MEASUREMENT_COLUMN = 'meas'
VALUE_COLUMN = 'val'
SAMPLE_COLUMN = 'samp'

# Jinja template replacements to decouple column names from the source
# tables from the dictionary keys used in this pipeline.
DATA_QUERY_REPLACEMENTS = {
    'MEASUREMENT_COLUMN': MEASUREMENT_COLUMN,
    'SAMPLE_COLUMN': SAMPLE_COLUMN,
    'VALUE_COLUMN': VALUE_COLUMN
}


def sample_measurements_to_example(sample, sample_measurements):
  """Convert sparse measurements to TensorFlow Example protocol buffers.

  See also
  https://www.tensorflow.org/versions/r0.10/how_tos/reading_data/index.html

  Args:
    sample: the identifier for the sample
    sample_measurements: list of the sample's sparse measurements

  Returns:
    A filled in TensorFlow Example proto for this sample.
  """
  feature_tuples = [(str(cnt[MEASUREMENT_COLUMN]), cnt[VALUE_COLUMN])
                    for cnt in sample_measurements]
  measurements, values = map(list, zip(*feature_tuples))
  features = {
      SAMPLE_NAME_FEATURE:
          tf.train.Feature(bytes_list=tf.train.BytesList(value=[str(sample)])),
      # These are tf.VarLenFeature.
      MEASUREMENTS_FEATURE:
          tf.train.Feature(bytes_list=tf.train.BytesList(value=measurements)),
      VALUES_FEATURE:
          tf.train.Feature(float_list=tf.train.FloatList(value=values))
  }

  return tf.train.Example(features=tf.train.Features(feature=features))


def measurements_to_examples(input_data):
  """Converts sparse measurements to TensorFlow Example protos.

  Args:
    input_data: dictionary objects with keys from
      DATA_QUERY_REPLACEMENTS

  Returns:
    TensorFlow Example protos.
  """
  meas_kvs = input_data | 'BucketMeasurements' >> beam.Map(
      lambda row: (row[SAMPLE_COLUMN], row))

  sample_meas_kvs = meas_kvs | 'GroupBySample' >> beam.GroupByKey()

  examples = (
      sample_meas_kvs
      | 'SamplesToExamples' >>
      beam.Map(lambda (key, vals): sample_measurements_to_example(key, vals)))

  return examples


class PreprocessOptions(PipelineOptions):

  @classmethod
  def _add_argparse_args(cls, parser):
    parser.add_argument(
        '--output',
        required=True,
        help='Output directory to which to write results.')
    parser.add_argument(
        '--input',
        required=True,
        help='Jinja file holding the query for the sample data.')


def run(argv=None):
  """Runs the sparse measurements preprocess pipeline.

  Args:
    argv: Pipeline options as a list of arguments.
  """
  pipeline_options = PipelineOptions(flags=argv)
  preprocess_options = pipeline_options.view_as(PreprocessOptions)
  cloud_options = pipeline_options.view_as(GoogleCloudOptions)
  output_dir = os.path.join(preprocess_options.output,
                            datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
  pipeline_options.view_as(SetupOptions).save_main_session = True
  pipeline_options.view_as(
      WorkerOptions).autoscaling_algorithm = 'THROUGHPUT_BASED'
  cloud_options.staging_location = os.path.join(output_dir, 'tmp', 'staging')
  cloud_options.temp_location = os.path.join(output_dir, 'tmp')
  cloud_options.job_name = 'preprocess-measurements-%s' % (
      datetime.datetime.now().strftime('%y%m%d-%H%M%S'))

  data_query = str(
      Template(open(preprocess_options.input, 'r').read()).render(
          DATA_QUERY_REPLACEMENTS))
  logging.info('data query : %s', data_query)

  with beam.Pipeline(options=pipeline_options) as p:
    # Read the table rows into a PCollection.
    rows = p | 'ReadMeasurements' >> beam.io.Read(
        beam.io.BigQuerySource(query=data_query, use_standard_sql=True))

    # Convert the data into TensorFlow Example Protocol Buffers.
    examples = measurements_to_examples(rows)

    # Write the serialized compressed protocol buffers to Cloud Storage.
    _ = (examples
         | 'EncodeExamples'
         >> beam.Map(lambda example: example.SerializeToString())
         | 'WriteExamples' >> tfrecordio.WriteToTFRecord(
             file_path_prefix=os.path.join(output_dir, 'examples'),
             compression_type=CompressionTypes.GZIP,
             file_name_suffix='.tfrecord.gz'))


if __name__ == '__main__':
  run()
