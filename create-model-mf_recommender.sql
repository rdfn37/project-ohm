CREATE OR REPLACE MODEL `project-ohm-******.ecom_core.mf_recommender`
OPTIONS(
  MODEL_TYPE='MATRIX_FACTORIZATION',
  USER_COL='user_id',
  ITEM_COL='product_id',
  RATING_COL='rating',
  NUM_FACTORS=32,
  L2_REG=0.1,
  MAX_ITERATIONS=20
) AS
SELECT user_id, product_id, rating
FROM `project-ohm-******.ecom_core.v_interactions_for_ml`;
