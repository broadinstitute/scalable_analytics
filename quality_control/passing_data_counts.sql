#standardSQL
  --
  -- Count the number of distinct cells and genes in this dataset.
  --
SELECT
  COUNT(DISTINCT gene) AS passing_gene_cnt,
  COUNT(DISTINCT cell) AS passing_cell_cnt
FROM
  `{{ RAW_DATA_TABLE }}`
WHERE
  cell IN (
    SELECT
      cell
    FROM
      `{{ PASSING_CELLS_TABLE }}`)
  AND
  gene IN (
    SELECT
      gene
    FROM
      `{{ PASSING_GENES_TABLE }}`)
