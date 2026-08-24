"""Low-latency Kafka telemetry consumer and benchmark recorder."""

import argparse
import csv
import json
import os
import time

from kafka import KafkaConsumer, TopicPartition


RESULT_FIELDS = [
    "pipeline",
    "input_rate",
    "events_generated",
    "events_processed",
    "average_latency_ms",
    "minimum_latency_ms",
    "maximum_latency_ms",
    "throughput_events_per_sec",
]


def append_result(path: str, result: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process telemetry immediately from Kafka")
    parser.add_argument("--topic", default="telemetry")
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--group", default="telemetry-streaming")
    parser.add_argument("--manual-assignment", action="store_true")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--expected-events", type=int, default=0)
    parser.add_argument("--input-rate", type=float, default=0.0)
    parser.add_argument("--offset-reset", choices=("earliest", "latest"), default="latest")
    parser.add_argument("--results", default="results/benchmark_results.csv")
    args = parser.parse_args()

    consumer = KafkaConsumer(
        bootstrap_servers=args.bootstrap,
        group_id=None if args.manual_assignment else args.group,
        auto_offset_reset=args.offset_reset,
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
    if args.manual_assignment:
        partitions = consumer.partitions_for_topic(args.topic) or set()
        if not partitions:
            raise RuntimeError(f"Kafka topic has no available partitions: {args.topic}")
        assigned_partitions = [TopicPartition(args.topic, partition) for partition in partitions]
        consumer.assign(assigned_partitions)
        if args.offset_reset == "latest":
            consumer.seek_to_end(*assigned_partitions)
    latencies = []
    started = time.monotonic()
    print(f"Streaming consumer listening on {args.topic}")
    try:
        while time.monotonic() - started < args.timeout:
            try:
                records = consumer.poll(timeout_ms=200, max_records=500)
            except ValueError as error:
                print(f"Kafka poll interrupted: {error}. Saving collected measurements.")
                break
            for messages in records.values():
                for message in messages:
                    event = message.value
                    latency = (time.time() - event["timestamp"]) * 1000
                    latencies.append(latency)
                    print(f"Processed event {event['event_id']} | latency={latency:.2f} ms")
                    if args.expected_events and len(latencies) >= args.expected_events:
                        break
                if args.expected_events and len(latencies) >= args.expected_events:
                    break
            if args.expected_events and len(latencies) >= args.expected_events:
                break
    finally:
        if not args.manual_assignment:
            consumer.commit()
        consumer.close()

    elapsed = max(time.monotonic() - started, 0.001)
    if latencies:
        result = {
            "pipeline": "streaming",
            "input_rate": args.input_rate,
            "events_generated": args.expected_events or len(latencies),
            "events_processed": len(latencies),
            "average_latency_ms": round(sum(latencies) / len(latencies), 3),
            "minimum_latency_ms": round(min(latencies), 3),
            "maximum_latency_ms": round(max(latencies), 3),
            "throughput_events_per_sec": round(len(latencies) / elapsed, 3),
        }
        append_result(args.results, result)
        print(
            f"Streaming finished: {len(latencies)} events | "
            f"average latency={result['average_latency_ms']} ms | "
            f"throughput={result['throughput_events_per_sec']}/sec"
        )
    else:
        print("Streaming finished: no events processed")


if __name__ == "__main__":
    main()
