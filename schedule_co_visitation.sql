CREATE OR REPLACE TABLE `project-ohm-******.ecom_core.co_visitation`
CLUSTER BY product_a, product_b AS
WITH session_events AS (
  SELECT session_id, user_id, product_id, event_ts,
         ROW_NUMBER() OVER(PARTITION BY session_id ORDER BY event_ts) AS rn
  FROM `project-ohm-******.ecom_core.fact_events`
  WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
),
pairs AS (
  SELECT a.product_id AS product_a, b.product_id AS product_b
  FROM session_events a
  JOIN session_events b
    ON a.session_id = b.session_id
   AND a.rn < b.rn
   AND TIMESTAMP_DIFF(b.event_ts, a.event_ts, MINUTE) BETWEEN 0 AND 30
)
SELECT product_a, product_b, COUNT(*) AS co_occurrences
FROM pairs
GROUP BY product_a, product_b
HAVING co_occurrences >= 2;
