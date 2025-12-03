CREATE OR REPLACE VIEW `project-ohm-******.ecom_core.v_interactions_for_ml` AS
SELECT
  user_id,
  product_id,
  CASE
    WHEN event_type = 'purchase' THEN 3.0
    WHEN event_type = 'add_to_cart' THEN 1.5
    ELSE 1.0
  END AS rating
FROM `project-ohm-******.ecom_core.fact_events`
WHERE event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND user_id IS NOT NULL
  AND product_id IS NOT NULL;
