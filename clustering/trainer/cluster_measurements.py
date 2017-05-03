# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
"""Tensorflow implementation of sparse measurement clustering."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


import tensorflow as tf

from tensorflow.contrib.learn.python.learn import learn_runner as learn_runner
from tensorflow.contrib.learn.python.learn.estimators import kmeans as kmeans_lib
from tensorflow.contrib.learn.python.learn.utils import input_fn_utils
from tensorflow.contrib.learn.python.learn.utils import saved_model_export_utils
from tensorflow.python import debug as tf_debug
from tensorflow.python.lib.io.tf_record import TFRecordCompressionType

from trainer.shared_constants import *

# Keys for the serving input function.
EXAMPLE_KEY = "input_feature"
DENSE_KEY = "dense"

tf.flags.DEFINE_bool("use_cosine_distance", False,
                     "Override the default of euclidean distance to instead "
                     "use cosine distance.")
tf.flags.DEFINE_bool("use_kmeans_plus_plus", False,
                     "Override the default of random initialization to "
                     "instead use kmeans++ initialization.")
tf.flags.DEFINE_float("relative_tolerance", None,
                      "Threshold at which to stop training when the change "
                      "in loss goes below this tolerance.")
tf.flags.DEFINE_string("vocabulary_file", None,
                       "Newline-separated file of the names of the subset of "
                       "measurements, or all possible measurements, in the "
                       "tf.Example protos to be used for clustering.")
tf.flags.DEFINE_integer("num_clusters", None,
                        "The number of clusters to learn from the data.")
tf.flags.DEFINE_integer("batch_size", 50,
                        "The size of the training input batches.")
tf.flags.DEFINE_string("input_file_pattern", None, "Path to the input files.")
tf.flags.DEFINE_string("output_path", None,
                       "Output directory used by the local and cloud jobs.")
tf.flags.DEFINE_integer("num_train_steps", 100,
                        "Number of training iterations.")
tf.flags.DEFINE_string("id_field", "sample_name",
                       "The name of the field that contains the sample ids.")
tf.flags.DEFINE_integer("save_checkpoints_secs", 600,
                        "The number of seconds to elapse before a checkpoint "
                        "is saved.")
tf.flags.DEFINE_integer("export_every_n_steps", 1000,
                        "The number of steps to occur between exports.")
tf.flags.DEFINE_boolean("debug", False, "Enable tensorflow debugger."
                        "https://www.tensorflow.org/programmers_guide/debugger")

FLAGS = tf.flags.FLAGS


def _get_feature_columns():
  """Generates a dictionary of `FeatureColumn` objects for our inputs.

  Returns:
    Dictionary of `FeatureColumn` objects.
  """
  return {
      SAMPLE_NAME_FEATURE: tf.FixedLenFeature(shape=[], dtype=tf.string),
      MEASUREMENTS_FEATURE: tf.VarLenFeature(dtype=tf.string),
      VALUES_FEATURE: tf.VarLenFeature(dtype=tf.float32)
  }


def _raw_features_to_dense_tensor(raw_features):
  """Convert the raw features expressing a sparse vector to a dense tensor.

  Args:
    raw_features: Parsed features in sparse matrix format.
  Returns:
    A dense tensor populated with the raw features.
  """
  # Load the vocabulary here as each batch of examples is parsed to ensure that
  # the examples and the mapping table are located in the same TensorFlow graph.
  measurement_table = tf.contrib.lookup.index_table_from_file(
      vocabulary_file=FLAGS.vocabulary_file)
  tf.logging.info("Loaded vocabulary file %s with %s terms.",
                  FLAGS.vocabulary_file, str(measurement_table.size()))

  indices = measurement_table.lookup(raw_features[MEASUREMENTS_FEATURE])

  merged = tf.sparse_merge(
      indices,
      raw_features[VALUES_FEATURE],
      vocab_size=measurement_table.size())
  return tf.sparse_tensor_to_dense(merged)


def _input_fn():
  """Supplies the training input to the model.

  Returns:
    A tuple consisting of 1) a dictionary of tensors whose keys are
    the feature names, and 2) a tensor of target labels which for
    clustering must be 'None'.
  """

  tf.logging.info("Reading files from %s", FLAGS.input_file_pattern)
  input_files = sorted(list(tf.gfile.Glob(FLAGS.input_file_pattern)))
  tf.logging.info("Reading files %s", input_files)

  def gzip_reader():
    return tf.TFRecordReader(options=tf.python_io.TFRecordOptions(
        compression_type=TFRecordCompressionType.GZIP))

  raw_features = tf.contrib.learn.io.read_batch_features(
      file_pattern=input_files,
      batch_size=FLAGS.batch_size,
      randomize_input=True,
      reader=gzip_reader,
      features=_get_feature_columns())

  dense = _raw_features_to_dense_tensor(raw_features)

  return dense, None


def _predict_input_fn():
  """Supplies the input to the model.

  Returns:
    A tuple consisting of 1) a dictionary of tensors whose keys are
    the feature names, and 2) a tensor of target labels which for
    clustering must be 'None'.
  """

  # Add a placeholder for the serialized tf.Example proto input.
  examples = tf.placeholder(tf.string, shape=(None,), name="examples")

  raw_features = tf.parse_example(examples, _get_feature_columns())

  dense = _raw_features_to_dense_tensor(raw_features)

  return input_fn_utils.InputFnOps(
      features={DENSE_KEY: dense},
      labels=None,
      default_inputs={EXAMPLE_KEY: examples})


def create_experiment_fn(output_dir=None):
  """Experiment function."""
  distance_metric = (tf.contrib.factorization.COSINE_DISTANCE
                     if FLAGS.use_cosine_distance
                     else tf.contrib.factorization.SQUARED_EUCLIDEAN_DISTANCE)
  initial_clusters = (tf.contrib.factorization.KMEANS_PLUS_PLUS_INIT
                      if FLAGS.use_kmeans_plus_plus
                      else tf.contrib.factorization.RANDOM_INIT)

  # Create estimator
  kmeans = kmeans_lib.KMeansClustering(
      FLAGS.num_clusters,
      model_dir=output_dir,
      initial_clusters=initial_clusters,
      distance_metric=distance_metric,
      use_mini_batch=True,
      relative_tolerance=FLAGS.relative_tolerance,
      config=tf.contrib.learn.RunConfig(
          save_checkpoints_secs=FLAGS.save_checkpoints_secs))

  train_monitors = []
  if FLAGS.debug:
    train_monitors.append(tf_debug.LocalCLIDebugHook())

  return tf.contrib.learn.Experiment(
      estimator=kmeans,
      train_steps=FLAGS.num_train_steps,
      eval_steps=1,
      eval_input_fn=_input_fn,
      train_input_fn=_input_fn,
      train_monitors=train_monitors,
      export_strategies=[saved_model_export_utils.make_export_strategy(
          _predict_input_fn,
          exports_to_keep=5)]
  )


def main(unused_argv):
  if not FLAGS.input_file_pattern:
    raise ValueError("Input file pattern should be specified.")

  if not FLAGS.vocabulary_file:
    raise ValueError("Vocabulary file should be specified.")

  if not FLAGS.output_path:
    raise ValueError("Output path should be specified.")

  if not FLAGS.num_clusters:
    raise ValueError("Number of classes should be specified.")

  if FLAGS.num_clusters > FLAGS.batch_size:
    raise ValueError("Number of classes should be less than "
                     "or equal to the batch size.")

  learn_runner.run(experiment_fn=create_experiment_fn,
                   output_dir=FLAGS.output_path)


if __name__ == "__main__":
  tf.logging.set_verbosity(tf.logging.INFO)
  tf.app.run()
