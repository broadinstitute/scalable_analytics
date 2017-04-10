#standardSQL
  --
  -- Compute cell counts per cluster.
  --
SELECT
  cluster,
  COUNT(cell) AS cnt
FROM
  `{{ CLUSTER_TABLE }}` AS clust
GROUP BY
  cluster
ORDER BY
  cluster
