CREATE OR REPLACE TABLE `project-ohm-******.ecom_core.product_popularity`
PARTITION BY partition_date
CLUSTER BY product_id, category AS
SELECT
  e.product_id,
  p.category,
  COUNTIF(event_type = 'view') AS views,
  COUNTIF(event_type = 'purchase') AS purchases,
  SUM(IF(event_type = 'purchase', e.price * e.quantity, 0)) AS revenue,
  CURRENT_DATE() AS partition_date
FROM `project-ohm-******.ecom_core.fact_events` AS e
LEFT JOIN `project-ohm-******.ecom_core.dim_products` AS p USING (product_id)
WHERE e.event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY e.product_id, p.category, partition_date;
