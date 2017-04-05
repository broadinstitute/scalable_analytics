#!/usr/bin/env python

# Copyright 2017 Verily Life Sciences Inc.
#
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

r"""Convert a dense matrix of positive values to sparse, long format.

Example Input:
,cell1,cell2,cell3
gene1,0.0,0.0,3.0
gene2,0.0,0.0,0.0
gene3,1.0,0.0,2.0

Example Output:
cell1,gene3,1.0
cell3,gene1,3.0
cell3,gene3,2.0

It is very fast (~4 minutes for a 2 GB CSV) when run on Compute Engine
utilizing streaming download and upload.
https://cloud.google.com/storage/docs/gsutil/commands/cp#streaming-transfers

For uncompressed CSV files:

chmod a+x dense_to_long.py ; \
  gsutil cat \
  gs://BUCKET-NAME/PATH/TO/INPUT/FILE.csv
  \
  | \
  ./dense_to_long.py \
  | \
  gsutil cp - gs://BUCKET-NAME/PATH/TO/OUTPUT/FILE.csv

For compressed CSV files, use the appropriate command to unzip the file
before passing it to this script:

chmod a+x dense_to_long.py ; \
  gsutil cat \
  gs://BUCKET-NAME/PATH/TO/INPUT/FILE.csv.gz
  | \
  gunzip \
  | \
  ./dense_to_long.py \
  | \
  gsutil cp - gs://BUCKET-NAME/PATH/TO/OUTPUT/FILE.csv
"""

import sys

header = sys.stdin.readline().strip()
samples = header.split(",")
num_cols = len(samples)

# Emit the output CSV file header.
sys.stdout.write(",".join(["cell", "gene", "trans_cnt"]) + "\n")

for line in sys.stdin:
  trimmed = line.strip()
  if not trimmed:
    break

  values = trimmed.split(",")
  if len(values) != num_cols:
    raise ValueError("Not all rows in the CSV have the same number of " +
                     "columns: %d != %d" % (len(values), num_cols))

  measurement = values[0]
  for i in range(1, num_cols):
    if float(values[i]) > 0:
      # Emit the greater than zero measurement in sparse matrix format.
      sys.stdout.write(",".join([samples[i], measurement, values[i]]) + "\n")

