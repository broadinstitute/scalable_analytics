#standardSQL
  --
  -- Identify genes that pass the quality control criteria.  These thresholds are based on
  -- those in https://github.com/broadinstitute/BipolarCell2016.  Update them as needed for
  -- the data to which they are being applied.
  --
SELECT
  gene
FROM
  `{{ GENE_METRICS_TABLE }}`
WHERE
  30 < cell_cnt
  AND 60 < alltrans
