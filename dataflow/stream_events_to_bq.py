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

# Validate that all required variables are present
if not all([PROJECT_ID, BQ_DATASET, BQ_TABLE, PUBSUB_SUBSCRIPTION, TEMP_BUCKET]):
    raise RuntimeError("Variáveis de ambiente faltando. Confira o arquivo .env.")

print(PROJECT_ID)
print(BQ_DATASET)
print(BQ_TABLE)
print(PUBSUB_SUBSCRIPTION)
print(TEMP_BUCKET)

# Set default project for Google Cloud libraries to ensure they know which project to use
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", PROJECT_ID)
os.environ.setdefault("GCLOUD_PROJECT", PROJECT_ID)

# BigQuery schema definition
# This must match the schema of the destination table in BigQuery
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
    """
    A DoFn (Do Function) that processes each element in the PCollection.
    It parses the raw JSON message from Pub/Sub and maps it to the BigQuery schema.
    """

    def process(self, message):
        # Decode the Pub/Sub message payload from bytes to string
        payload = message.decode("utf-8")
        event = json.loads(payload)

        # Extract basic fields
        user_id = event.get("user_id")
        product_id = event.get("product_id")
        event_type = event.get("event_type")
        event_ts = event.get("event_ts")

        # Generate a UUID for event_id if it's missing
        event_id = event.get("event_id") or str(uuid.uuid4())

        # Extract the date (YYYY-MM-DD) from the timestamp for partitioning
        event_date = None
        if event_ts:
            event_date = event_ts[:10]

        # Construct the row dictionary matching the BigQuery schema
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
            "attributes": json.dumps(
                event.get("attributes", {})
            ),  # Convert dict to JSON string
        }

        yield row


def run(argv=None):
    pipeline_options = PipelineOptions()

    # Set standard options (streaming mode is required for Pub/Sub)
    standard_options = pipeline_options.view_as(StandardOptions)
    standard_options.streaming = True

    # Set Google Cloud options (Project ID)
    gcloud_options = pipeline_options.view_as(GoogleCloudOptions)
    gcloud_options.project = PROJECT_ID

    # Define the pipeline structure
    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            # Step 1: Read messages from the Pub/Sub subscription
            | "ReadFromPubSub"
            >> beam.io.ReadFromPubSub(subscription=PUBSUB_SUBSCRIPTION)
            # Step 2: Parse JSON and map to BigQuery row format
            | "ParseAndMapEvent" >> beam.ParDo(ParseAndMapEvent())
            # Step 3: Write the rows to BigQuery
            | "WriteToBigQuery"
            >> beam.io.WriteToBigQuery(
                table=f"{PROJECT_ID}:{BQ_DATASET}.{BQ_TABLE}",
                schema=BQ_SCHEMA,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,  # Append to existing table
                create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER,  # Do not create table if missing
                custom_gcs_temp_location=f"gs://{TEMP_BUCKET}/dataflow-bq-temp",  # Temp location for BQ loads
            )
        )


if __name__ == "__main__":
    run()
