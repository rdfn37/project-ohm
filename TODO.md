# Phase 2 — Feature Engineering Guide

1) Align schemas and staging
- [x] Ensure `fact_events` is populated and partitioned by `event_date`; confirm clustering on `user_id`, `product_id`.
- [x] Verify base dimensions (`dim_users`, `dim_products`) with keys/attributes needed for grouping (category, brand, device). (Dim_products backfilled.)

2) Define feature tables and contracts
- [x] Target tables/views: `user_daily_activity`, `user_product_interactions`, `product_popularity`, `co_visitation`, `product_features`, `user_features`, optional `product_embeddings`.
- [x] Set retention windows (e.g., 30d for most aggregates, 90d for co-visitation).

3) Build core aggregations (BigQuery SQL)
- [x] Daily user activity (`user_daily_activity`).
- [x] Product popularity by category (`product_popularity`).
- [x] User–product interactions with recency (`user_product_interactions`).
- [x] Session/window-based co-visitation pairs (`co_visitation`).

4) Scheduling and freshness
- [x] Use BigQuery scheduled queries (daily/hourly) with rolling windows.
- [ ] For near-real-time, populate `_staging` tables (last 1–2 days) and MERGE into mains (optional).
- [ ] Consider materialized views where patterns allow (optional).

5) Partitioning/clustering
- [x] Partition by date; cluster by access keys (user_id for user tables; product_id/category for product tables; product_a/product_b for co-visitation).

6) Data quality and validation
- [x] Add checks: daily row counts, null-rate on keys, event_type distribution, recency sanity.
- [ ] Optionally log results into a small `dq_results` table.

7) Optional embeddings placeholder
- [x] Define `product_embeddings(product_id, embedding ARRAY<FLOAT64>, updated_at)` even if empty.
- [ ] Later: BigQuery ML matrix factorization or Vertex pipelines.

8) Wire to downstream consumers
- [ ] Document feature contracts: which tables feed candidate generation vs ranking.
- [ ] Provide example queries for top-N per user/product (outside the console snippets).

9) Operability
- [ ] Alert on scheduled query failures; set email/Slack notifications.
- [ ] Monitor slot usage and query cost; validate clustering effectiveness.

# Phase 3 — Baseline Models (BigQuery ML)

1) Prep training data
- [x] Create view `v_interactions_for_ml` with 30d interactions and a rating/weight (e.g., purchase=3, add_to_cart=1.5, view=1).
- [ ] Optionally filter to purchases only if you prefer explicit feedback (not applied).

2) Train baseline model (matrix factorization)
- [x] Train `mf_recommender` using USER_COL=user_id, ITEM_COL=product_id, RATING_COL=rating; set factors/regularization/iterations.
- [ ] Store in `ecom_core` with versioning (currently single name).

3) Validate/evaluate
- [x] Holdout split via FARM_FINGERPRINT modulus; run `ML.EVALUATE` on the holdout.
- [x] Inspect metrics (rmse, precision/recall@K if available).

4) Serve queries
- [x] Add sample `ML.RECOMMEND` query for top-N per user.
- [x] Add sample similar-items query (co_visitation-based for now; item-context MF recommend unsupported in this build).
- [x] Document cold-start fallback: use `product_popularity` for new users/items.

5) Scheduling/retraining
- [x] Create scheduled query to refresh the view and retrain daily/weekly (overwrite).
- [ ] Optionally keep last N models for rollback (versioned models).

6) Optional enhancements
- [x] Blend MF scores with popularity/category priors.
- [ ] Add content features later (Vertex or feature tables) and move to a two-stage ranker.

# Phase 4 — Recommendations API (Cloud Run)

1) API design & contracts
- [ ] Define endpoints: GET `/recommend/{user_id}`, GET `/similar/{product_id}`, (optional) `/trending`, `/top-category/{category}`.
- [ ] Define response schema (e.g., list of {product_id, score, source, category, pop_score, blended_score}, paging).
- [ ] Decide cold-start behavior (use popularity by default; optional category hint).

2) Service implementation
- [ ] Choose language/runtime (e.g., Python FastAPI or Node/Express).
- [ ] Implement handlers that call BigQuery:
  - User recs: use blended or MF script; cold-start fallback built-in.
  - Similar items: use `co_visitation` fallback; later, item factors if supported.
  - Trending/top-category: query `product_popularity`.
- [ ] Apply deterministic ordering and limits; parameterize `top_k`.

3) Config & secrets
- [ ] Wire service account for BigQuery access (least privilege; read-only).
- [ ] Configure env vars (PROJECT_ID, DATASET, MODEL_NAME, REGION, etc.).
- [ ] Add optional cache toggle and alpha/top_k defaults.

4) Deployment (Cloud Run)
- [ ] Create Dockerfile/Cloud Build config.
- [ ] Deploy to Cloud Run with min instances = 0 or 1; set concurrency appropriately.
- [ ] Set IAM/auth (public vs. authenticated; consider IAP or API key if needed).

5) Validation & monitoring
- [ ] Add a small smoke test endpoint (`/healthz`).
- [ ] Log request/response metadata (user_id/item_id, latency, branch used).
- [ ] Set basic alerts on errors/latency via Cloud Monitoring.

6) Optional extras
- [ ] Add simple response cache for repeat requests (in-memory or Redis/Memorystore).
- [ ] Add rate limiting if exposing publicly.
