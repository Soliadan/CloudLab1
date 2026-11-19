
import json
import logging
import os
import time

import boto3
from database_pg import get_connection


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

QUEUE_URL = os.environ["SQS_QUEUE_URL"]
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

sqs = boto3.client("sqs", region_name=AWS_REGION)


def process_order(data):
    """Save an order to PostgreSQL."""

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO orders
            (id, parfume_name, volume, brand, order_date, price)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                data["id"],
                data["parfume_name"],
                data["Volume"],
                data["brand"],
                data["order_date"],
                data["price"]
            )
        )

    logging.info("Order processed: %s", data["id"])


def main():
    logging.info("SQS worker started")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )

            messages = response.get("Messages", [])

            for message in messages:
                try:
                    data = json.loads(message["Body"])

                    process_order(data)

                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"]
                    )

                    logging.info("Message deleted from SQS")

                except Exception:
                    logging.exception(
                        "Message processing failed"
                    )

        except Exception:
            logging.exception("SQS connection error")
            time.sleep(5)


if __name__ == "__main__":
    main()
