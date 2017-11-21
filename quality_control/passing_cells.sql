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
  {{ PASSING_MT_FRACTION }} > mttrans/alltrans
  AND gene_cnt BETWEEN {{ MIN_GENES }} AND {{ MAX_GENES }}
