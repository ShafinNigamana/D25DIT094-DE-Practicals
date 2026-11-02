"""Generate latency and throughput comparison charts from the saved benchmark data."""

from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_PATH = PROJECT_ROOT / "results" / "performance_results.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_recent_results(results_path: Path) -> pd.DataFrame:
    """Return the latest valid ETL and ELT rows from the results file."""
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    results = pd.read_csv(results_path)
    if results.empty:
        raise ValueError("No benchmark rows found in results/performance_results.csv")

    results["timestamp"] = pd.to_datetime(results["timestamp"], errors="coerce")
    results = results.dropna(subset=["pipeline", "timestamp"]).copy()

    if results.empty:
        raise ValueError("No valid benchmark rows found in results/performance_results.csv")

    latest = results.sort_values("timestamp").groupby("pipeline", group_keys=False).tail(1).copy()

    for column in ["latency_ms", "throughput_events_per_sec"]:
        if column not in latest.columns:
            latest[column] = float("nan")

    for idx, row in latest.iterrows():
        total_time = pd.to_numeric(row.get("total_time_seconds"), errors="coerce")
        output_rows = pd.to_numeric(row.get("output_rows"), errors="coerce")

        if pd.notna(row.get("latency_ms")):
            latency_ms = pd.to_numeric(row["latency_ms"], errors="coerce")
        else:
            latency_ms = total_time * 1000.0 if pd.notna(total_time) else None

        if pd.notna(row.get("throughput_events_per_sec")):
            throughput = pd.to_numeric(row["throughput_events_per_sec"], errors="coerce")
        elif pd.notna(total_time) and pd.notna(output_rows) and total_time > 0:
            throughput = output_rows / total_time
        else:
            throughput = None

        latest.at[idx, "latency_ms"] = latency_ms
        latest.at[idx, "throughput_events_per_sec"] = throughput

    return latest


def create_latency_chart(latest: pd.DataFrame, output_path: Path) -> None:
    """Create the ETL vs ELT latency comparison chart."""
    etl_row = latest[latest["pipeline"] == "ETL"].iloc[0]
    elt_row = latest[latest["pipeline"] == "ELT"].iloc[0]

    labels = ["ETL", "ELT"]
    values = [
        float(pd.to_numeric(etl_row["latency_ms"], errors="coerce")),
        float(pd.to_numeric(elt_row["latency_ms"], errors="coerce")),
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=["#4C72B0", "#DD8452"])
    ax.set_title("ETL vs ELT Latency Comparison")
    ax.set_xlabel("Pipeline")
    ax.set_ylabel("Latency (ms)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar, value in zip(bars, values):
        if pd.notna(value):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max(values) * 0.02,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def create_throughput_chart(latest: pd.DataFrame, output_path: Path) -> None:
    """Create the ETL vs ELT throughput comparison chart."""
    etl_row = latest[latest["pipeline"] == "ETL"].iloc[0]
    elt_row = latest[latest["pipeline"] == "ELT"].iloc[0]

    labels = ["ETL", "ELT"]
    values = [
        float(pd.to_numeric(etl_row["throughput_events_per_sec"], errors="coerce")),
        float(pd.to_numeric(elt_row["throughput_events_per_sec"], errors="coerce")),
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=["#55A868", "#C44E52"])
    ax.set_title("ETL vs ELT Throughput Comparison")
    ax.set_xlabel("Pipeline")
    ax.set_ylabel("Throughput (events/sec)")
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    for bar, value in zip(bars, values):
        if pd.notna(value):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max(values) * 0.02,
                f"{value:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    """Read performance results and generate latency and throughput charts."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    latest = load_recent_results(RESULTS_PATH)

    latency_path = OUTPUT_DIR / "latency_comparison.png"
    throughput_path = OUTPUT_DIR / "throughput_comparison.png"

    create_latency_chart(latest, latency_path)
    create_throughput_chart(latest, throughput_path)

    print(f"Latency chart saved to: {latency_path}")
    print(f"Throughput chart saved to: {throughput_path}")


if __name__ == "__main__":
    main()
