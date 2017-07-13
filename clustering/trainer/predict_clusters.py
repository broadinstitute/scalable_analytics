# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
"""Beam pipeline wrapping TensorFlow implementation of cluster prediction.

See also:
https://cloud.google.com/solutions/using-cloud-dataflow-for-batch-predictions-with-tensorflow
https://github.com/GoogleCloudPlatform/dataflow-prediction-example
"""

import logging

import apache_beam as beam
from apache_beam.io import tfrecordio
from apache_beam.io.filesystem import CompressionTypes
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.options.pipeline_options import WorkerOptions
import tensorflow as tf

# The KMeansClustering import is not used in the python code below, but
# it is necessary to import it so that the TensorFlow Ops used by the
# saved model are loaded into the runtime environment.
from tensorflow.contrib.learn import KMeansClustering
from trainer.shared_constants import SAMPLE_NAME_FEATURE

# BigQuery column name constants.
SAMPLE = 'cell'
CLUSTER = 'cluster'


class PredictOptions(PipelineOptions):

  @classmethod
  def _add_argparse_args(cls, parser):
    parser.add_argument(
        '--model', required=True, help='Path to the saved TensorFlow model.')
    parser.add_argument(
        '--output',
        required=True,
        help='Output BigQuery table for results specified as: '
        'PROJECT:DATASET.TABLE or DATASET.TABLE.')
    parser.add_argument('--input', required=True, help='Path to input files.')


def get_table_schema():
  """Formulate the schema for the destination table."""

  fields = [(SAMPLE, 'string', 'required'), (CLUSTER, 'integer', 'required')]
  from apache_beam.io.gcp.internal.clients import bigquery  # pylint: disable=wrong-import-order, wrong-import-position
  table_schema = bigquery.TableSchema()
  for (col_name, col_type, col_mode) in fields:
    field_schema = bigquery.TableFieldSchema()
    field_schema.name = col_name
    field_schema.type = col_type
    field_schema.mode = col_mode
    table_schema.fields.append(field_schema)
  return table_schema


class PredictDoFn(beam.DoFn):
  """DoFn to pass the input data through TensorFlow to obtain the prediction.

    This class restores the saved model and runs the subset of tensors that
    perform prediction.
  """
  INPUT_TENSOR = 'examples:0'
  CLUSTER_CLASSIFICATION_TENSOR = 'Squeeze_1:0'

  def __init__(self, model_export_dir):
    self.model_export_dir = model_export_dir

  def start_bundle(self):
    with tf.Graph().as_default() as graph:
      sess = tf.InteractiveSession()
      meta_graph_def = tf.saved_model.loader.load(
          sess, [tf.saved_model.tag_constants.SERVING], self.model_export_dir)
    signature_def = meta_graph_def.signature_def[
        tf.saved_model.signature_constants.DEFAULT_SERVING_SIGNATURE_DEF_KEY]
    self.input_tensor = signature_def.inputs[
        tf.saved_model.signature_constants.CLASSIFY_INPUTS].name
    self.input_tensors = [str(x.name) for x in signature_def.inputs.values()]
    if self.INPUT_TENSOR not in self.input_tensors:
      raise ValueError('Expected input tensor %s not in %s with keys %s',
                       self.INPUT_TENSOR,
                       self.input_tensors,
                       signature_def.inputs.keys())
    self.output_tensors = [str(x.name) for x in signature_def.outputs.values()]
    if self.CLUSTER_CLASSIFICATION_TENSOR not in self.output_tensors:
      raise ValueError('Expected cluster classification output tensor %s '
                       'not in %s with keys %s',
                       self.CLUSTER_CLASSIFICATION_TENSOR,
                       self.output_tensors,
                       signature_def.outputs.keys())

    self.sess = sess

  def predict(self, serialized_example):
    input_list = [serialized_example]
    output = self.sess.run(
        [self.CLUSTER_CLASSIFICATION_TENSOR],
        feed_dict={self.INPUT_TENSOR: input_list})
    example = tf.train.Example.FromString(serialized_example)
    return (example.features.feature[SAMPLE_NAME_FEATURE].bytes_list.value[0],
            output[0])

  def process(self, element):
    output_key, predicted_cluster = self.predict(element)
    return [{SAMPLE: output_key, CLUSTER: predicted_cluster}]


def run(argv=None):
  """Runs the sparse measurements prediction pipeline.

  Args:
    argv: Pipeline options as a list of arguments.
  """
  pipeline_options = PipelineOptions(flags=argv)
  predict_options = pipeline_options.view_as(PredictOptions)
  pipeline_options.view_as(SetupOptions).save_main_session = True
  pipeline_options.view_as(
      WorkerOptions).autoscaling_algorithm = 'THROUGHPUT_BASED'

  with beam.Pipeline(options=pipeline_options) as p:
    examples = (p | 'ReadExamples' >> tfrecordio.ReadFromTFRecord(
        file_pattern=predict_options.input,
        compression_type=CompressionTypes.GZIP))

    predictions = examples | 'Predict' >> beam.ParDo(
        PredictDoFn(model_export_dir=predict_options.model))

    _ = predictions | 'WriteTableRows' >> beam.io.Write(
        beam.io.BigQuerySink(
            predict_options.output,
            schema=get_table_schema(),
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED))


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  run()
