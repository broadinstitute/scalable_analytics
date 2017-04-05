#standardSQL
  --
  -- Identify cells that pass the quality control criteria.  These thresholds are based on
  -- those in https://github.com/broadinstitute/BipolarCell2016.  Update them as needed for
  -- the data to which they are being applied.
  --
SELECT
  cell
FROM
  `{{ CELL_METRICS_TABLE }}`
WHERE
  .10 > mttrans/alltrans
  AND 500 < gene_cnt
