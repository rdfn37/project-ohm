import json
import uuid
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import (
    PipelineOptions,
    StandardOptions,
    GoogleCloudOptions,
)
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET")
BQ_TABLE = os.getenv("BQ_TABLE")
PUBSUB_SUBSCRIPTION = os.getenv("PUBSUB_SUBSCRIPTION")
TEMP_BUCKET = os.getenv("TEMP_BUCKET")
REGION = os.getenv("REGION", "us-central1")  # <- new variable, with default

# Validate that all required variables are present
if not all([PROJECT_ID, BQ_DATASET, BQ_TABLE, PUBSUB_SUBSCRIPTION, TEMP_BUCKET]):
    raise RuntimeError("Variáveis de ambiente faltando. Confira o arquivo .env.")

print("PROJECT_ID:", PROJECT_ID)
print("BQ_DATASET:", BQ_DATASET)
print("BQ_TABLE:", BQ_TABLE)
print("PUBSUB_SUBSCRIPTION:", PUBSUB_SUBSCRIPTION)
print("TEMP_BUCKET:", TEMP_BUCKET)
print("REGION:", REGION)

# Set default project for Google Cloud libraries
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", PROJECT_ID)
os.environ.setdefault("GCLOUD_PROJECT", PROJECT_ID)

# BigQuery schema definition
BQ_SCHEMA = {
    "fields": [
        {"name": "event_id", "type": "STRING", "mode": "NULLABLE"},
        {"name": "user_id", "type": "STRING", "mode": "NULLABLE"},
        {"name": "session_id", "type": "STRING", "mode": "NULLABLE"},
        {"name": "product_id", "type": "STRING", "mode": "NULLABLE"},
        {"name": "event_type", "type": "STRING", "mode": "NULLABLE"},
        {"name": "event_ts", "type": "TIMESTAMP", "mode": "NULLABLE"},
        {"name": "event_date", "type": "DATE", "mode": "NULLABLE"},
        {"name": "quantity", "type": "INT64", "mode": "NULLABLE"},
        {"name": "price", "type": "NUMERIC", "mode": "NULLABLE"},
        {"name": "currency", "type": "STRING", "mode": "NULLABLE"},
        {"name": "source", "type": "STRING", "mode": "NULLABLE"},
        {"name": "attributes", "type": "JSON", "mode": "NULLABLE"},
    ]
}


class ParseAndMapEvent(beam.DoFn):
    def process(self, message):
        payload = message.decode("utf-8")
        event = json.loads(payload)

        user_id = event.get("user_id")
        product_id = event.get("product_id")
        event_type = event.get("event_type")
        event_ts = event.get("event_ts")

        event_id = event.get("event_id") or str(uuid.uuid4())

        event_date = None
        if event_ts:
            event_date = event_ts[:10]

        row = {
            "event_id": event_id,
            "user_id": user_id,
            "session_id": event.get("session_id"),
            "product_id": product_id,
            "event_type": event_type,
            "event_ts": event_ts,
            "event_date": event_date,
            "quantity": event.get("quantity", 1),
            "price": event.get("price"),
            "currency": event.get("currency"),
            "source": event.get("source"),
            "attributes": json.dumps(event.get("attributes", {})),
        }

        yield row


def run(argv=None):
    # **IMPORTANT**: using argv enables using flags on command line
    pipeline_options = PipelineOptions(argv)

    # Streaming mode
    standard_options = pipeline_options.view_as(StandardOptions)
    standard_options.streaming = True

    # GCP / Dataflow options
    gcloud_options = pipeline_options.view_as(GoogleCloudOptions)
    gcloud_options.project = PROJECT_ID
    gcloud_options.region = REGION
    # We use the same TEMP bucket for the Dataflow job's staging/temp
    gcloud_options.staging_location = f"gs://{TEMP_BUCKET}/dataflow-staging"
    gcloud_options.temp_location = f"gs://{TEMP_BUCKET}/dataflow-tmp"
    # job_name can come from CLI or use default
    if not gcloud_options.job_name:
        gcloud_options.job_name = "stream-events-to-bq"

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | "ReadFromPubSub"
            >> beam.io.ReadFromPubSub(subscription=PUBSUB_SUBSCRIPTION)
            | "ParseAndMapEvent" >> beam.ParDo(ParseAndMapEvent())
            | "WriteToBigQuery"
            >> beam.io.WriteToBigQuery(
                table=f"{PROJECT_ID}:{BQ_DATASET}.{BQ_TABLE}",
                schema=BQ_SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,
                custom_gcs_temp_location=f"gs://{TEMP_BUCKET}/dataflow-bq-temp",
            )
        )


if __name__ == "__main__":
    run()
