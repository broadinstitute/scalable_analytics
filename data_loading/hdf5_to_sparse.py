#!/usr/bin/env python

# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

r"""Convert a particular hdf5 file to sparse, long format.

This code is based loosely on
http://cf.10xgenomics.com/supp/cell-exp/megacell_tutorial.html
and is hardcoded to load
https://support.10xgenomics.com/single-cell/datasets/1M_neurons
"""

import sys
import argparse
import collections
import numpy as np
import os
import scipy.sparse as sp_sparse
import tables

GENOME = 'mm10'

# This dsub-compatible script will read configuration from the environment,
# if available.
DEFAULT_BEGIN_IDX = os.getenv('BEGIN_IDX', 0)  # First cell in the file.
DEFAULT_END_IDX = os.getenv('END_IDX', 1306127)  # Last cell in the file.
DEFAULT_INPUT_FILE = os.getenv('INPUT_FILE',
                               '1M_neurons_filtered_gene_bc_matrices_h5.h5')
DEFAULT_OUTPUT_FILE = os.getenv('OUTPUT_FILE')

np.random.seed(0)

GeneBCMatrix = collections.namedtuple(
    'GeneBCMatrix',
    ['gene_ids', 'gene_names', 'barcodes', 'matrix'])


def get_matrix_from_h5(filename, genome):
  """Load the matrix from the HDF5 file.

  Code is from http://cf.10xgenomics.com/supp/cell-exp/megacell_tutorial.html

  Args:
    filename: HDF5 filename
    genome: Genome of data in the file.

  Returns:
    the sparse matrix of data
  """
  with tables.open_file(filename, 'r') as f:
    try:
      dsets = {}
      for node in f.walk_nodes('/' + genome, 'Array'):
        dsets[node.name] = node.read()
      matrix = sp_sparse.csc_matrix(
          (dsets['data'], dsets['indices'], dsets['indptr']),
          shape=dsets['shape'])
      return GeneBCMatrix(
          dsets['genes'], dsets['gene_names'], dsets['barcodes'], matrix)
    except tables.NoSuchNodeError:
      raise Exception('Genome %s does not exist in %s.' % (genome, filename))
    except KeyError:
      raise Exception('File %s missing one or more required datasets.'
                      % filename)


def run(argv=None):
  """Runs the variant preprocess pipeline.

  Args:
    argv: Pipeline options as a list of arguments.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--begin-idx',
      type=int,
      default=DEFAULT_BEGIN_IDX,
      help='Index with which to start reading data (inclusive).')
  parser.add_argument(
      '--end-idx',
      type=int,
      default=DEFAULT_END_IDX,
      help='Index at which to stop reading data (exclusive).')
  parser.add_argument(
      '--input-file',
      default=DEFAULT_INPUT_FILE,
      help='Input file path.')
  parser.add_argument(
      '--output-file',
      default=DEFAULT_OUTPUT_FILE,
      help='Output file path. If None, stdout will be used.')
  args = parser.parse_args(argv)

  sys.stderr.write('Processing cells [%d,%d) from file %s'
                   % (args.begin_idx, args.end_idx, args.input_file))
  mm10_gbm = get_matrix_from_h5(args.input_file, GENOME)

  handle = open(args.output_file, 'w') if args.output_file else sys.stdout

  # Emit the output CSV file header.
  handle.write(','.join(['gene_id', 'gene', 'cell', 'trans_cnt']) + '\n')

  for cell in range(args.begin_idx, args.end_idx):
    for sparse_idx in range(mm10_gbm.matrix.indptr[cell],
                            mm10_gbm.matrix.indptr[cell+1]):
      dense_idx = mm10_gbm.matrix.indices[sparse_idx]
      handle.write(','.join([mm10_gbm.gene_ids[dense_idx],
                             mm10_gbm.gene_names[dense_idx],
                             mm10_gbm.barcodes[cell],
                             str(mm10_gbm.matrix.data[sparse_idx])])
                   + '\n')

  if handle is not sys.stdout:
    handle.close()


if __name__ == '__main__':
  run()
