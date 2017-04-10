#standardSQL
--
-- Compute differential gene expression of one cluster compared to all others.
-- This method is ported from the R implementation in
-- https://github.com/broadinstitute/BipolarCell2016.
--
CREATE TEMP FUNCTION bq_pbinom(k FLOAT64, n FLOAT64, p FLOAT64)
  RETURNS FLOAT64
  LANGUAGE js AS
"""
  return pbinom(k, n, p);
"""
OPTIONS (
  library=["{{ EXTERNAL_JAVA_SCRIPT_LIBRARY }}"]
);
  -------------------------------------------------
  -- Sub queries.
  --
WITH
  --
  --  Select the relevant data from the cluster table.
  --
  cell_groups AS (
  SELECT
    cell,
    cluster = {{ ONE_CLUSTER }} AS cell_in_selected_cluster
  FROM
    `{{ CLUSTER_TABLE }}`
  WHERE
    -- Typically clustering is only performed on passing cells, so this extra
    -- check is redundant but included for clarity.
    cell IN (
      SELECT
        cell
      FROM
        `{{ PASSING_CELLS_TABLE }}`)
  ),
  --
  --  Count the number of cells present in each cluster.
  --
  cell_group_counts AS (
  SELECT
    COUNTIF(cell_in_selected_cluster) AS num_cells_clusSelected,
    COUNTIF(NOT cell_in_selected_cluster) AS num_cells_clusRest
  FROM
    cell_groups
  ),
  --
  -- Obtain the passing transcript counts, joining with cluster.
  --
  cluster_transcripts AS (
  SELECT
    gene,
    cell,
    trans_cnt,
    cluster = {{ ONE_CLUSTER }} AS cell_in_selected_cluster
  FROM
    `{{ RAW_DATA_TABLE }}` AS trans
  JOIN
    `{{ CLUSTER_TABLE }}` AS clusters
  USING(cell)
  WHERE
    gene IN (
    SELECT
      gene
    FROM
      `{{ PASSING_GENES_TABLE }}`)
    AND trans.cell IN (
    SELECT
      cell
    FROM
      `{{ PASSING_CELLS_TABLE }}`) ),
  --
  -- Compute some counts for cells in the selected cluster versus cells in all
  -- other clusters.
  --
  expressed_cell_counts AS (
  SELECT
    gene,
    COUNTIF(cell_in_selected_cluster) AS num_cells_expr_clusSelected,
    COUNTIF(NOT cell_in_selected_cluster) AS num_cells_expr_clusRest,
    SUM(IF(cell_in_selected_cluster,
        trans_cnt,
        0)) AS trans_cnt_clusSelected,
    SUM(IF(NOT cell_in_selected_cluster,
        trans_cnt,
        0)) AS trans_cnt_clusRest
  FROM
    cluster_transcripts
  GROUP BY
    gene),
  --
  -- Compute mean transcript count. Also add 1 to unexpressed
  -- markers to avoid false positives.
  --
  regularized_cell_counts AS (
  SELECT
    gene,
    num_cells_expr_clusSelected,
    num_cells_expr_clusRest,
    IF(num_cells_expr_clusSelected > 0,
      num_cells_expr_clusSelected,
      1) AS reg_num_cells_expr_clusSelected,
    IF(num_cells_expr_clusRest > 0,
      num_cells_expr_clusRest,
      1) AS reg_num_cells_expr_clusRest,
    trans_cnt_clusSelected,
    trans_cnt_clusRest
  FROM
    expressed_cell_counts),
  --
  -- Compute pvalues.
  --
  pvalues AS (
  SELECT
    gene,
    num_cells_expr_clusSelected,
    num_cells_expr_clusRest,
    num_cells_clusSelected,
    num_cells_clusRest,
    ROUND(trans_cnt_clusSelected
      / num_cells_clusSelected, 3) AS mean_trans_cnt_clusSelected,
    ROUND(trans_cnt_clusRest/num_cells_clusRest, 3) AS mean_trans_cnt_clusRest,
    IF(num_cells_expr_clusRest > 0
      AND num_cells_expr_clusSelected > 0,
      LOG((num_cells_expr_clusSelected * num_cells_clusRest)
        / (num_cells_expr_clusRest * num_cells_clusSelected)),
      0) AS log_effect,
    bq_pbinom(num_cells_clusSelected - num_cells_expr_clusSelected,
      num_cells_clusSelected,
      1 - reg_num_cells_expr_clusRest/num_cells_clusRest) AS pv1,
    bq_pbinom(num_cells_clusRest - num_cells_expr_clusRest,
      num_cells_clusRest,
      1 - reg_num_cells_expr_clusSelected/num_cells_clusSelected) AS pv2
  FROM
    regularized_cell_counts CROSS JOIN cell_group_counts)
  -------------------------------------------------
  -- Main query.
  --
SELECT
  gene,
  IF(log_effect > 0, pv1, pv2) AS pv,
  log_effect,
  mean_trans_cnt_clusSelected,
  mean_trans_cnt_clusRest
FROM
  pvalues
WHERE
  ABS(log_effect) >= LOG(2)
  AND num_cells_expr_clusSelected/num_cells_clusSelected > 0.1
ORDER BY
  log_effect DESC
