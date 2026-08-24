"""Run comparable Kafka micro-batch and streaming experiments."""

import argparse
import os
import subprocess
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_trial(pipeline: str, rate: float, duration: float, args: argparse.Namespace) -> None:
    consumer_script = os.path.join(
        ROOT,
        "batch",
        "batch_processor.py",
    ) if pipeline == "batch" else os.path.join(ROOT, "streaming", "streaming_consumer.py")
    consumer_timeout = duration + args.batch_interval + 8
    consumer_command = [
        sys.executable,
        consumer_script,
        "--topic",
        args.topic,
        "--bootstrap",
        args.bootstrap,
        "--group",
        f"benchmark-{pipeline}-{time.time_ns()}",
        "--timeout",
        str(consumer_timeout),
        "--input-rate",
        str(rate),
        "--offset-reset",
        "latest",
        "--results",
        args.results,
        "--manual-assignment",
    ]
    if pipeline == "batch":
        consumer_command.extend(["--batch-interval", str(args.batch_interval)])

    producer_command = [
        sys.executable,
        os.path.join(ROOT, "data", "telemetry_producer.py"),
        "--topic",
        args.topic,
        "--bootstrap",
        args.bootstrap,
        "--rate",
        str(rate),
        "--duration",
        str(duration),
    ]
    expected_events = max(1, int(round(rate * duration)))
    consumer_command.extend(["--expected-events", str(expected_events)])

    print(f"\nStarting {pipeline} trial at {rate:g} events/sec for {duration:g}s")
    consumer = subprocess.Popen(consumer_command, cwd=ROOT)
    try:
        time.sleep(4)
        producer = subprocess.run(producer_command, cwd=ROOT, check=True)
        print(f"Producer exit code: {producer.returncode}")
        consumer.wait(timeout=consumer_timeout + 10)
    except subprocess.TimeoutExpired:
        consumer.terminate()
        consumer.wait()
        raise RuntimeError(f"{pipeline} consumer exceeded its timeout")
    finally:
        if consumer.poll() is None:
            consumer.terminate()
            consumer.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run measured batch and streaming Kafka trials")
    parser.add_argument("--topic", default="telemetry")
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--rates", nargs="+", type=float, default=[100, 500, 1000])
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--batch-interval", type=float, default=5.0)
    parser.add_argument("--results", default="results/benchmark_results.csv")
    parser.add_argument("--clear-results", action="store_true")
    args = parser.parse_args()

    if args.clear_results and os.path.exists(args.results):
        os.remove(args.results)
    for rate in args.rates:
        for pipeline in ("batch", "streaming"):
            run_trial(pipeline, rate, args.duration, args)
    print(f"\nBenchmark complete. Results: {args.results}")


if __name__ == "__main__":
    main()
