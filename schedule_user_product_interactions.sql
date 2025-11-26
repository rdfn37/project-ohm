CREATE OR REPLACE TABLE `project-ohm-******.ecom_core.user_product_interactions`
PARTITION BY partition_date
CLUSTER BY user_id, product_id AS
SELECT
  user_id,
  product_id,
  COUNT(*) AS interactions,
  COUNTIF(event_type='purchase') AS purchases,
  MAX(event_ts) AS last_event_ts,
  CURRENT_DATE() AS partition_date
FROM `project-ohm-******.ecom_core.fact_events`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY user_id, product_id, partition_date;
