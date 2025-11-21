CREATE TABLE `project-ohm-******.ecom_core.fact_events`
(
  -- Core identifiers
  event_id      STRING,        -- Optional: UUID for dedup
  user_id       STRING,
  session_id    STRING,        -- Can be NULL at first
  product_id    STRING,
  
  -- Event info
  event_type    STRING,        -- "view", "add_to_cart", "purchase", etc.
  event_ts      TIMESTAMP,     -- Event timestamp (from client or server)
  event_date    DATE,          -- DATE(event_ts) for partitioning

  -- Optional but handy later
  quantity      INT64,         -- For cart/purchase events, default 1
  price         NUMERIC,       -- Price at event time (for revenue)
  currency      STRING,        -- e.g. "USD", "BRL"
  source        STRING,        -- e.g. "web", "mobile", "email", "organic"

  -- Free-form properties (JSON) so you don't have to change schema all the time
  attributes    JSON           -- e.g. {"device": "mobile", "referrer": "google"}
)
PARTITION BY event_date
CLUSTER BY user_id, product_id;
