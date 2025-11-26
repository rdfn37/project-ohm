# Project Ohm — Streaming E-commerce Events to BigQuery

Pipeline for ingesting raw e-commerce events from Pub/Sub into a BigQuery analytics model, plus helpers to seed test traffic and DDLs for the warehouse tables.

## Repository layout
- dataflow/stream_events_to_bq.py — Apache Beam streaming job (Dataflow runner) from Pub/Sub to BigQuery.
- create-table-*.sql — DDL for ecom_core dataset (facts and dimensions).
- tools/event-generator/generate_events.py — Pub/Sub traffic generator for synthetic events.
- events-raw-topic.json — Example Pub/Sub message payload.
- check_gcp_account.py — Quick check of active GCP project/identity via ADC.
- requirements.txt — Python dependencies.

## Prerequisites
- Python 3.10+ and pip.
- Google Cloud project with billing enabled.
- A Pub/Sub topic events-raw and a subscription for the Dataflow job (e.g., events-raw-sub).
- BigQuery dataset ecom_core.
- GCS bucket for Dataflow staging/temp files (e.g., ohm-temp-bucket).
- Application Default Credentials (gcloud auth application-default login or a service account key) configured locally.

## Setup
1) Install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Configure environment (.env at repo root)
```env
PROJECT_ID=your-project-id
BQ_DATASET=ecom_core
BQ_TABLE=fact_events            # table the pipeline writes to
PUBSUB_SUBSCRIPTION=projects/your-project-id/subscriptions/events-raw-sub
TEMP_BUCKET=ohm-temp-bucket     # without gs://
REGION=us-central1              # optional; defaults to us-central1
```

3) Create warehouse tables
```bash
bq query --use_legacy_sql=false < create-table-dim_users.sql
bq query --use_legacy_sql=false < create-table-dim_products.sql
bq query --use_legacy_sql=false < create-table-fact_event.sql
bq query --use_legacy_sql=false < create-table-fact_orders.sql
bq query --use_legacy_sql=false < create-table-fact_order_items.sql
```

## Running the pipeline (Dataflow)
Example launch (runner v2 recommended):
```bash
python dataflow/stream_events_to_bq.py \
  --runner DataflowRunner \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --job_name stream-events-$(date +%Y%m%d%H%M) \
  --experiments=use_runner_v2
```
Notes:
- Staging/temp locations are derived from TEMP_BUCKET (gs://$TEMP_BUCKET/dataflow-staging and /dataflow-tmp).
- Streaming mode is enabled in the script.
- The pipeline writes to BQ_DATASET.BQ_TABLE using the schema defined in stream_events_to_bq.py.

## Generating test traffic
Publish synthetic events to the events-raw topic:
```bash
export PROJECT_ID=your-project-id  # or use .env + python-dotenv
python tools/event-generator/generate_events.py
```
Each event is logged as it’s published; adjust the sleep interval or payload logic as needed.

## Event payload example
See events-raw-topic.json:
```json
{
  "user_id": "u123",
  "product_id": "p456",
  "event_type": "view",
  "event_ts": "2025-11-19T15:12:00Z",
  "session_id": "s789",
  "quantity": 1,
  "price": 39.90,
  "currency": "BRL",
  "source": "web",
  "attributes": {"device": "mobile", "referrer": "google"}
}
```

## Helpful checks
- python check_gcp_account.py — confirms ADC project and principal.
- Monitor Dataflow/BigQuery metrics in the GCP console; Pub/Sub dead-letter if you add one.

## Troubleshooting
- Missing env vars: pipeline raises on startup. Revisit .env.
- Permissions: ensure the principal running Dataflow has Pub/Sub subscriber and BigQuery data editor, and storage access to the temp bucket.
- Schema errors: confirm BQ_TABLE matches the DDL provided and is in CREATE_NEVER mode in the pipeline.

## Next steps
- Add dashboarding/BI queries on top of fact_events.
- Extend the generator to simulate more event types or traffic patterns.
- Add dead-letter handling for malformed messages.
