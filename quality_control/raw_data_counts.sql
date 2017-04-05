#standardSQL
  --
  -- Count the number of distinct cells and genes in this dataset.
  --
SELECT
  COUNT(DISTINCT gene) AS gene_cnt,
  COUNT(DISTINCT cell) AS cell_cnt
FROM
  `{{ RAW_DATA_TABLE }}`
