#standardSQL
  --
  -- Compute the number of all transcripts and mitochondrial transcripts per cell.
  --
SELECT
  cell,
  SUM(trans_cnt) AS alltrans,
  SUM(IF(gene IN (SELECT gene FROM `{{ MT_GENE_TABLE }}`),
      trans_cnt,
      0)) AS mttrans,
  COUNT(DISTINCT gene) AS gene_cnt
FROM
  `{{ RAW_DATA_TABLE }}`
WHERE
  trans_cnt > 0
GROUP BY
  cell
