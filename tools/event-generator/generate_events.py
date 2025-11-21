import json
import random
import time
import uuid
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from google.cloud import pubsub_v1

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
print(f"PROJECT_ID: {PROJECT_ID}")
TOPIC_ID = "events-raw"
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

# Mock data lists for generating random events
USERS = [f"u{i}" for i in range(1, 1001)]  # Generates ['u1', 'u2', ..., 'u1000']
PRODUCTS = [f"p{i}" for i in range(1, 501)]  # Generates ['p1', 'p2', ..., 'p500']
EVENT_TYPES = ["view", "add_to_cart", "purchase"]
SOURCES = ["web", "mobile", "email"]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def random_event():
    """Generates a single random e-commerce event."""
    user_id = random.choice(USERS)
    product_id = random.choice(PRODUCTS)

    # Weighted random choice for event type
    # 70% view, 20% add_to_cart, 10% purchase
    event_type = random.choices(
        EVENT_TYPES,
        weights=[0.7, 0.2, 0.1],
        k=1,
    )[0]

    # Generate a random session ID
    session_id = f"s-{uuid.uuid4().hex[:8]}"

    # Logic for quantity and price
    quantity = 1 if event_type == "view" else random.randint(1, 3)
    price = round(random.uniform(10.0, 200.0), 2)

    event = {
        "user_id": user_id,
        "product_id": product_id,
        "event_type": event_type,
        "event_ts": now_iso(),
        "session_id": session_id,
        "quantity": quantity,
        "price": price,
        "currency": "BRL",
        "source": random.choice(SOURCES),
        "attributes": {
            "device": random.choice(["mobile", "desktop"]),
            "referrer": random.choice(["google", "facebook", "direct", "email"]),
        },
    }

    return event


def publish_event(event: dict):
    """Publishes a single event to the Pub/Sub topic."""
    # Convert dictionary to JSON string, then to bytes (required by Pub/Sub)
    data = json.dumps(event).encode("utf-8")

    # Publish the message
    future = publisher.publish(topic_path, data=data)

    # Wait for the publish to complete (blocking call)
    future.result()
    print(
        "Published event:",
        event["event_type"],
        "user:",
        event["user_id"],
        "product:",
        event["product_id"],
    )


def main():
    """Main loop to generate and publish events continuously."""
    while True:
        event = random_event()
        publish_event(event)
        # Wait 0.5 seconds before sending the next event
        time.sleep(0.5)


if __name__ == "__main__":
    main()
