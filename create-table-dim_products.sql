CREATE TABLE `project-ohm-******.ecom_core.dim_products`
(
  product_id      STRING,       -- Primary key (match fact_events.product_id)
  sku             STRING,       -- Optional
  name            STRING,
  description     STRING,
  category        STRING,       -- e.g. "pizza", "drink", "dessert"
  brand           STRING,       -- Optional
  price           NUMERIC,      -- Current price
  currency        STRING,       -- e.g. "USD", "BRL"
  image_url       STRING,       -- For frontend/demo later
  is_active       BOOL,         -- Soft delete / availability
  created_at      TIMESTAMP,
  updated_at      TIMESTAMP
);
