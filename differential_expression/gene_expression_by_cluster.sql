#standardSQL
  --
  -- Compute aggregate gene expression for cells in each cluster.
  --
WITH
  --
  --  Count the number of cells present in each cluster.
  --
  count_cells AS (
  SELECT
    cluster,
    COUNT(cell) AS cluster_cells_cnt
  FROM
    `{{ CLUSTER_TABLE }}`
  GROUP BY
    cluster),
  --
  -- For each gene, count the number of cells in each cluster that express
  -- it. Keep in mind that the raw data table does not include rows when the
  -- transcript count for a particular cell and gene is zero.
  --
  count_transcripts AS (
  SELECT
    gene,
    cluster,
    SUM(trans_cnt) AS cluster_trans_cnt,
    COUNT(1) AS cluster_expr_cells_cnt
  FROM
    `{{ CLUSTER_TABLE }}` AS clust
  LEFT JOIN
    `{{ RAW_DATA_TABLE }}` AS trans USING(cell)
  GROUP BY
    gene,
    cluster)
  --
  -- Combine these two types of counts to determine our final metrics
  -- for a particular subset of genes.
  --
SELECT
  gene,
  cluster,
  SAFE_DIVIDE(cluster_trans_cnt,
    cluster_expr_cells_cnt) AS avg_trans_cnt,
  cluster_expr_cells_cnt/cluster_cells_cnt AS perc_expr
FROM
  count_cells
LEFT OUTER JOIN
  count_transcripts USING(cluster)
WHERE
  gene IN ({{ MARKER_GENE_LIST }})
