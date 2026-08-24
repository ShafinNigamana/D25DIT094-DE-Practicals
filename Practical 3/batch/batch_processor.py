"""Periodic Kafka micro-batch processor for telemetry events."""

import argparse
import csv
import json
import os
import time
from statistics import mean

import pandas as pd
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


def process_batch(events: list[dict], input_rate: float) -> dict:
    frame = pd.DataFrame(events)
    now = time.time()
    latencies = [(now - timestamp) * 1000 for timestamp in frame["timestamp"]]
    print(
        f"Batch {len(frame)} events | average CPU {frame['cpu_percent'].mean():.2f}% | "
        f"max CPU {frame['cpu_percent'].max():.2f}% | "
        f"average memory {frame['memory_percent'].mean():.2f}% | "
        f"average response {frame['response_time_ms'].mean():.2f} ms"
    )
    return {
        "pipeline": "batch",
        "input_rate": input_rate,
        "events_generated": len(frame),
        "events_processed": len(frame),
        "average_latency_ms": round(mean(latencies), 3),
        "minimum_latency_ms": round(min(latencies), 3),
        "maximum_latency_ms": round(max(latencies), 3),
        "throughput_events_per_sec": 0,
        "_latencies": latencies,
    }


def run(args: argparse.Namespace) -> None:
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
    batches = []
    total_processed = 0
    all_latencies = []
    started = time.monotonic()
    next_batch = started + args.batch_interval
    print(f"Micro-batch processor listening on {args.topic}; interval={args.batch_interval:g}s")

    try:
        while time.monotonic() - started < args.timeout:
            try:
                records = consumer.poll(timeout_ms=200, max_records=args.max_poll_records)
            except ValueError as error:
                print(f"Kafka poll interrupted: {error}. Processing the collected batch.")
                break
            for messages in records.values():
                batches.extend(message.value for message in messages)
            if batches and time.monotonic() >= next_batch:
                result = process_batch(batches, args.input_rate)
                total_processed += result["events_processed"]
                all_latencies.extend(result.pop("_latencies"))
                if not args.manual_assignment:
                    consumer.commit()
                batches.clear()
                next_batch = time.monotonic() + args.batch_interval
            if args.expected_events and total_processed >= args.expected_events:
                break
    finally:
        if batches:
            result = process_batch(batches, args.input_rate)
            total_processed += result["events_processed"]
            all_latencies.extend(result.pop("_latencies"))
        consumer.close()
    if all_latencies:
        elapsed = max(time.monotonic() - started, 0.001)
        append_result(args.results, {
            "pipeline": "batch",
            "input_rate": args.input_rate,
            "events_generated": total_processed,
            "events_processed": total_processed,
            "average_latency_ms": round(mean(all_latencies), 3),
            "minimum_latency_ms": round(min(all_latencies), 3),
            "maximum_latency_ms": round(max(all_latencies), 3),
            "throughput_events_per_sec": round(total_processed / elapsed, 3),
        })
    print(f"Micro-batch finished: {total_processed} events processed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Consume telemetry in periodic Pandas batches")
    parser.add_argument("--topic", default="telemetry")
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--group", default="telemetry-batch")
    parser.add_argument("--manual-assignment", action="store_true")
    parser.add_argument("--batch-interval", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--expected-events", type=int, default=0)
    parser.add_argument("--input-rate", type=float, default=0.0)
    parser.add_argument("--max-poll-records", type=int, default=500)
    parser.add_argument("--offset-reset", choices=("earliest", "latest"), default="latest")
    parser.add_argument("--results", default="results/benchmark_results.csv")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
