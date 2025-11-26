CREATE OR REPLACE TABLE `project-ohm-******.ecom_core.user_daily_activity`
PARTITION BY event_date
CLUSTER BY user_id AS
SELECT
  user_id,
  event_date,
  COUNT(*) AS events,
  COUNTIF(event_type='view') AS views,
  COUNTIF(event_type='add_to_cart') AS adds,
  COUNTIF(event_type='purchase') AS purchases,
  SUM(IF(event_type='purchase', price*quantity, 0)) AS revenue
FROM `project-ohm-******.ecom_core.fact_events`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY user_id, event_date;
