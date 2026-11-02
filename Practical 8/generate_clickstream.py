"""
generate_clickstream.py
Generates a realistic large clickstream dataset for Practical 8 (Query Processing and Optimization).
"""

import os
import time
import numpy as np
import pandas as pd

def generate_clickstream(output_path="clickstream.csv", num_records=500000):
    print(f"Generating {num_records:,} clickstream events...")
    start_time = time.time()
    
    np.random.seed(42)
    
    user_ids = np.random.randint(1000, 5000, size=num_records)
    session_ids = np.random.randint(100000, 200000, size=num_records)
    
    event_types = np.random.choice(
        ["page_view", "search", "add_to_cart", "checkout", "purchase"],
        size=num_records,
        p=[0.55, 0.20, 0.15, 0.06, 0.04]
    )
    
    page_urls = np.random.choice(
        ["/home", "/products/electronics", "/products/apparel", "/cart", "/checkout", "/help", "/deals"],
        size=num_records,
        p=[0.30, 0.20, 0.15, 0.15, 0.08, 0.06, 0.06]
    )
    
    devices = np.random.choice(["mobile", "desktop", "tablet"], size=num_records, p=[0.60, 0.32, 0.08])
    durations = np.random.exponential(scale=45.0, size=num_records).round(1)
    
    # Generate timestamps spanning 30 days
    base_timestamp = pd.Timestamp("2026-09-01 00:00:00").value // 10**9
    random_offsets = np.random.randint(0, 30 * 86400, size=num_records)
    event_times = pd.to_datetime(base_timestamp + random_offsets, unit="s")
    
    # Generate purchase amounts for purchases, 0 for other events
    purchase_amounts = np.where(
        event_types == "purchase",
        np.random.uniform(10.0, 500.0, size=num_records).round(2),
        0.0
    )
    
    df = pd.DataFrame({
        "event_id": np.arange(1, num_records + 1),
        "user_id": user_ids,
        "session_id": session_ids,
        "event_time": event_times,
        "event_type": event_types,
        "page_url": page_urls,
        "device": devices,
        "duration_sec": durations,
        "purchase_amount": purchase_amounts
    })
    
    df.to_csv(output_path, index=False)
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    elapsed = time.time() - start_time
    print(f"[OK] Generated {num_records:,} records in {elapsed:.2f}s -> {output_path} ({file_size_mb:.2f} MB)")
    return output_path

if __name__ == "__main__":
    generate_clickstream()
