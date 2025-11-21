CREATE TABLE `project-ohm-******.ecom_core.dim_users`
(
  user_id        STRING,        -- Primary key (match fact_events.user_id)
  created_at     TIMESTAMP,     -- When the user first appeared
  first_seen_ts  TIMESTAMP,     -- Could be same as created_at
  email          STRING,        -- Optional, for real systems
  country        STRING,
  city           STRING,
  device_type    STRING,        -- e.g. "mobile", "desktop"
  marketing_opt_in BOOL
);
