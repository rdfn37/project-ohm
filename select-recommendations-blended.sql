-- Blended recommendations: MF + popularity fallback/boost.
DECLARE target_user STRING DEFAULT 'u123';
DECLARE alpha FLOAT64 DEFAULT 0.7;  -- weight for MF score vs popularity
DECLARE top_k INT64 DEFAULT 10;

-- Popularity with normalized score
CREATE TEMP TABLE pop AS
SELECT
  product_id,
  category,
  views,
  purchases,
  revenue,
  SAFE_DIVIDE(views, NULLIF(MAX(views) OVER (), 0)) AS pop_score
FROM `project-ohm-******.ecom_core.product_popularity`;

-- Try MF recs for the target user
IF EXISTS (
  SELECT 1 FROM `project-ohm-******.ecom_core.v_interactions_for_ml`
  WHERE user_id = target_user
) THEN
  CREATE TEMP TABLE mf AS
  SELECT product_id, predicted_rating
  FROM (
    SELECT
      product_id,
      predicted_rating,
      ROW_NUMBER() OVER (ORDER BY predicted_rating DESC, product_id) AS rn
    FROM ML.RECOMMEND(
      MODEL `project-ohm-******.ecom_core.mf_recommender`,
      (SELECT target_user AS user_id)
    )
  )
  WHERE rn <= top_k * 3;  -- grab extra to blend before trimming

  SELECT
    target_user AS user_id,
    mf.product_id,
    mf.predicted_rating,
    COALESCE(pop.pop_score, 0) AS pop_score,
    alpha * mf.predicted_rating + (1 - alpha) * COALESCE(pop.pop_score, 0) AS blended_score
  FROM mf
  LEFT JOIN pop USING (product_id)
  QUALIFY ROW_NUMBER() OVER (ORDER BY blended_score DESC, product_id) <= top_k;
ELSE
  -- Cold-start: popularity only (deterministic order)
  SELECT
    NULL AS user_id,
    product_id,
    0.0 AS predicted_rating,
    pop_score,
    pop_score AS blended_score
  FROM pop
  QUALIFY ROW_NUMBER() OVER (ORDER BY pop_score DESC, purchases DESC, revenue DESC, product_id) <= top_k;
END IF;
