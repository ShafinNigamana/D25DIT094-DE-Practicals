"""Produce synthetic telemetry to a Kafka topic at a configurable rate."""

import argparse
import json
import time

from kafka import KafkaProducer

from telemetry_generator import event_stream


def main() -> None:
    parser = argparse.ArgumentParser(description="Send telemetry events to Kafka")
    parser.add_argument("--topic", default="telemetry")
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--rate", type=float, default=100.0)
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--start-id", type=int, default=1001)
    args = parser.parse_args()

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
        retries=5,
    )
    count = 0
    started = time.monotonic()
    try:
        for event in event_stream(args.rate, args.duration, args.start_id):
            producer.send(args.topic, event)
            count += 1
            if count % max(int(args.rate), 1) == 0:
                print(f"Produced {count} events")
        producer.flush()
    finally:
        producer.close()
    elapsed = max(time.monotonic() - started, 0.001)
    print(f"Producer finished: {count} events in {elapsed:.2f}s ({count / elapsed:.2f}/sec)")


if __name__ == "__main__":
    main()
