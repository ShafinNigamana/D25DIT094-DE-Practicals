"""Generate comparative charts from measured benchmark CSV rows."""

import argparse
import os

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot latency and throughput benchmark results")
    parser.add_argument("--input", default="results/benchmark_results.csv")
    parser.add_argument("--output-dir", default="results")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Benchmark file does not exist: {args.input}")
    frame = pd.read_csv(args.input)
    required = {"pipeline", "input_rate", "average_latency_ms", "throughput_events_per_sec"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Missing benchmark columns: {', '.join(sorted(missing))}")
    if frame.empty:
        raise ValueError("Benchmark file contains no measured rows")

    os.makedirs(args.output_dir, exist_ok=True)
    for metric, filename, ylabel, title in (
        ("average_latency_ms", "latency_comparison.png", "Average latency (ms)", "Latency vs input rate"),
        (
            "throughput_events_per_sec",
            "throughput_comparison.png",
            "Throughput (events/sec)",
            "Throughput vs input rate",
        ),
    ):
        figure, axis = plt.subplots(figsize=(8, 5))
        for pipeline, rows in frame.groupby("pipeline"):
            rows = rows.sort_values("input_rate")
            axis.plot(rows["input_rate"], rows[metric], marker="o", label=pipeline.title())
        axis.set_xlabel("Input rate (events/sec)")
        axis.set_ylabel(ylabel)
        axis.set_title(title)
        axis.grid(True, alpha=0.3)
        axis.legend()
        figure.tight_layout()
        figure.savefig(os.path.join(args.output_dir, filename), dpi=150)
        plt.close(figure)
        print(f"Saved {os.path.join(args.output_dir, filename)}")


if __name__ == "__main__":
    main()
