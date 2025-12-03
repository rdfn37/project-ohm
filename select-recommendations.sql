-- Script: Try MF recommendations for a user; if none, fall back to popularity.
DECLARE target_user STRING DEFAULT 'u123';

-- If the user exists in training data, use MF; otherwise go straight to popularity.
IF EXISTS (
  SELECT 1 FROM `project-ohm-******.ecom_core.v_interactions_for_ml`
  WHERE user_id = target_user
) THEN
  CREATE TEMP TABLE recs AS
  SELECT *
  FROM ML.RECOMMEND(
    MODEL `project-ohm-******.ecom_core.mf_recommender`,
    (SELECT target_user AS user_id)
  )
  ORDER BY predicted_rating DESC, product_id
  LIMIT 10;

  SELECT * FROM recs;
ELSE
  SELECT product_id, category, views, purchases, revenue
  FROM `project-ohm-******.ecom_core.product_popularity`
  ORDER BY views DESC, purchases DESC, revenue DESC, product_id
  LIMIT 10;
END IF;
