#standardSQL
  --
  -- Compute the number of all transcripts and passing cells per gene.
  --
SELECT
  gene,
  SUM(trans_cnt) AS alltrans,
  COUNT(DISTINCT cell) AS cell_cnt
FROM
  `{{ RAW_DATA_TABLE }}`
WHERE
  trans_cnt > 0
  AND cell IN (
  SELECT
    cell
  FROM
    `{{ PASSING_CELLS_TABLE }}`)
GROUP BY
  gene
