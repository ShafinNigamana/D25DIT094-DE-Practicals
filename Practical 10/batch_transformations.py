"""
batch_transformations.py
Practical 10: Batch Transformations
Performs filtering, cross-source enrichment, and rolling-window aggregations on IoT data.
"""

import os
import pandas as pd

def run_batch_pipeline():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("\n--------------------------------------------------")
    print("STEP 1: BATCH FILTERING AND ENRICHMENT")
    print("--------------------------------------------------")
    
    df_telemetry = pd.read_csv("data/iot_telemetry.csv")
    df_metadata = pd.read_csv("data/iot_metadata.csv")
    
    print(f"Loaded {len(df_telemetry)} raw telemetry records and {len(df_metadata)} device registry records.")
    
    # 1. Filtering
    initial_count = len(df_telemetry)
    # Check nulls
    valid_mask = df_telemetry["temperature"].notna() & (df_telemetry["battery_level"] >= 0)
    df_clean = df_telemetry[valid_mask].copy()
    dropped_count = initial_count - len(df_clean)
    print(f"[OK] Filtered out {dropped_count} corrupted records (null values or negative battery).")
    
    # 2. Cross-Source Enrichment
    df_enriched = pd.merge(df_clean, df_metadata, on="device_id", how="left")
    print(f"[OK] Enriched telemetry with device metadata. Columns: {list(df_enriched.columns)}")
    
    # 3. Rolling Window Aggregation
    df_enriched["event_time"] = pd.to_datetime(df_enriched["event_time"])
    df_enriched = df_enriched.sort_values("event_time")
    
    # Compute rolling 10-second averages and max vibration per device
    df_rolling = df_enriched.set_index("event_time")
    rolling_stats = (
        df_rolling.groupby("device_id")[["temperature", "vibration"]]
        .rolling("10s")
        .agg({"temperature": "mean", "vibration": ["mean", "max"]})
        .reset_index()
    )
    rolling_stats.columns = ["device_id", "window_end_time", "avg_temperature", "avg_vibration", "max_vibration"]
    
    df_enriched.to_csv("results/batch_enriched_telemetry.csv", index=False)
    rolling_stats.to_csv("results/batch_rolling_summary.csv", index=False)
    
    print(f"[OK] Saved batch enriched data -> results/batch_enriched_telemetry.csv")
    print(f"[OK] Saved batch rolling summary -> results/batch_rolling_summary.csv")
    print("\nSample Batch Rolling Aggregation:")
    print(rolling_stats.head(5).to_string(index=False))
    return df_enriched, rolling_stats

if __name__ == "__main__":
    run_batch_pipeline()
