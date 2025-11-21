CREATE TABLE `project-ohm-******.ecom_core.fact_orders`
(
  order_id       STRING,
  user_id        STRING,
  order_ts       TIMESTAMP,
  order_date     DATE,
  order_total    NUMERIC,
  currency       STRING,
  status         STRING,        -- "completed", "cancelled", ...
  payment_method STRING,        -- "card", "pix", ...
  attributes     JSON           -- Extra info if needed
)
PARTITION BY order_date
CLUSTER BY user_id;
