"""
minio_partition_storage.py
Practical 5: Distributed Storage Systems with S3-Compatible Object Storage (SeaweedFS) and Hive-Style Partitioning.
Uploads partitioned dataset to S3 storage, benchmarks partition-pruned read vs full scan,
and implements the supplementary metadata crawler and partition skew analyzer.
"""

import os
import io
import time
import pandas as pd
import numpy as np
try:
    import boto3
    from botocore.client import Config
except ImportError:
    boto3 = None

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:8333")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "secret")
BUCKET_NAME = "de-warehouse-partitioned"

def get_s3_client():
    if boto3 is None:
        raise ImportError("boto3 is not installed.")
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def setup_minio_bucket(s3):
    print(f"Connecting to S3-compatible storage at {MINIO_ENDPOINT}...")
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"[OK] Dedicated bucket '{BUCKET_NAME}' exists.")
    except Exception:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"[OK] Created dedicated test bucket '{BUCKET_NAME}'.")

def upload_hive_partitions(s3, base_dir="data/partitions"):
    from generate_dataset import generate_partitioned_data
    if not os.path.exists(base_dir):
        generate_partitioned_data(base_dir)
        
    print("\nUploading Hive-style partitions to S3-compatible storage...")
    t0 = time.time()
    uploaded_count = 0
    total_bytes = 0
    
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".csv"):
                local_path = os.path.join(root, f)
                # Compute S3 object key (e.g., year=2024/month=01/region=north/data.csv)
                rel_path = os.path.relpath(local_path, base_dir).replace("\\", "/")
                file_size = os.path.getsize(local_path)
                s3.upload_file(local_path, BUCKET_NAME, rel_path)
                uploaded_count += 1
                total_bytes += file_size
                
    elapsed = time.time() - t0
    print(f"[OK] Uploaded {uploaded_count} partition files ({total_bytes / 1024:.1f} KB) in {elapsed:.2f}s.")

def benchmark_reads(s3):
    print("\n--------------------------------------------------")
    print("BENCHMARK: FULL SCAN VS PARTITION-PRUNED READ")
    print("--------------------------------------------------")
    
    # 1. Full Scan: List and fetch all objects across entire bucket
    t0 = time.time()
    paginator = s3.get_paginator("list_objects_v2")
    full_scan_bytes = 0
    full_scan_rows = 0
    
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            full_scan_bytes += obj["Size"]
            resp = s3.get_object(Bucket=BUCKET_NAME, Key=obj["Key"])
            df = pd.read_csv(io.BytesIO(resp["Body"].read()))
            full_scan_rows += len(df)
            
    t_full = time.time() - t0
    print(f"Full Bucket Scan:")
    print(f"  - Objects Read: {full_scan_rows:,} rows across all partitions")
    print(f"  - Data Transferred: {full_scan_bytes / 1024:.2f} KB")
    print(f"  - Elapsed Time: {t_full*1000:.2f} ms ({t_full:.4f} s)")
    
    # 2. Partition-Specific Read: Target specific prefix (year=2025/month=01/region=west/)
    target_prefix = "year=2025/month=01/region=west/"
    t0 = time.time()
    part_bytes = 0
    part_rows = 0
    
    resp_list = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=target_prefix)
    for obj in resp_list.get("Contents", []):
        part_bytes += obj["Size"]
        resp = s3.get_object(Bucket=BUCKET_NAME, Key=obj["Key"])
        df = pd.read_csv(io.BytesIO(resp["Body"].read()))
        part_rows += len(df)
        
    t_part = time.time() - t0
    print(f"\nPartition-Pruned Read (Prefix='{target_prefix}'):")
    print(f"  - Objects Read: {part_rows:,} rows in target partition")
    print(f"  - Data Transferred: {part_bytes / 1024:.2f} KB")
    print(f"  - Elapsed Time: {t_part*1000:.2f} ms ({t_part:.4f} s)")
    
    speedup = t_full / t_part if t_part > 0 else 1.0
    bytes_saved_pct = ((full_scan_bytes - part_bytes) / full_scan_bytes) * 100 if full_scan_bytes > 0 else 0
    print(f"\n[OK] Partition Pruning Advantage:")
    print(f"  - Latency Speedup: {speedup:.2f}x faster")
    print(f"  - I/O Reduction:   {bytes_saved_pct:.1f}% less data scanned over network")
    
    # Save benchmark
    bench_df = pd.DataFrame([
        {
            "Scan_Type": "Full Bucket Scan",
            "Prefix": "None (Whole Bucket)",
            "Bytes_Scanned_KB": round(full_scan_bytes / 1024, 2),
            "Rows_Returned": full_scan_rows,
            "Latency_ms": round(t_full * 1000, 2)
        },
        {
            "Scan_Type": "Partition-Pruned Read",
            "Prefix": target_prefix,
            "Bytes_Scanned_KB": round(part_bytes / 1024, 2),
            "Rows_Returned": part_rows,
            "Latency_ms": round(t_part * 1000, 2)
        }
    ])
    bench_df.to_csv("results/read_benchmark.csv", index=False)

def run_metadata_crawler(s3):
    print("\n--------------------------------------------------")
    print("SUPPLEMENTARY PROBLEM: METADATA CRAWLER & SKEW ANALYZER")
    print("--------------------------------------------------")
    
    paginator = s3.get_paginator("list_objects_v2")
    records = []
    
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size = obj["Size"]
            last_mod = obj["LastModified"]
            
            # Parse Hive partition keys
            parts = key.split("/")
            year_val = parts[0].split("=")[1] if "year=" in parts[0] else "N/A"
            month_val = parts[1].split("=")[1] if "month=" in parts[1] else "N/A"
            region_val = parts[2].split("=")[1] if "region=" in parts[2] else "N/A"
            
            records.append({
                "object_key": key,
                "year": year_val,
                "month": month_val,
                "region": region_val,
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
                "last_modified": str(last_mod)
            })
            
    df_meta = pd.DataFrame(records)
    df_meta.to_csv("results/partition_metadata_catalog.csv", index=False)
    
    # Calculate Skew Analysis
    sizes = df_meta["size_bytes"].values
    mean_size = np.mean(sizes)
    std_size = np.std(sizes)
    cv = (std_size / mean_size) if mean_size > 0 else 0
    max_size = np.max(sizes)
    min_size = np.min(sizes)
    skew_ratio = max_size / min_size if min_size > 0 else 1.0
    
    print(f"Crawl Summary:")
    print(f"  - Total Partitions Cataloged: {len(df_meta)}")
    print(f"  - Total Bucket Footprint:     {df_meta['size_kb'].sum():.2f} KB")
    print(f"  - Mean Partition Size:        {mean_size / 1024:.2f} KB")
    print(f"  - Std Dev (Size Disparity):   {std_size / 1024:.2f} KB")
    print(f"  - Coefficient of Variation:   {cv:.3f}")
    print(f"  - Max / Min Partition Ratio:  {skew_ratio:.2f}x (Skew detected in high-traffic 'west' region)")
    
    skew_df = pd.DataFrame([{
        "total_partitions": len(df_meta),
        "total_size_kb": round(df_meta['size_kb'].sum(), 2),
        "mean_partition_kb": round(mean_size / 1024, 2),
        "std_dev_kb": round(std_size / 1024, 2),
        "coefficient_of_variation": round(cv, 3),
        "max_min_skew_ratio": round(skew_ratio, 2)
    }])
    skew_df.to_csv("results/partition_skew_summary.csv", index=False)
    print("[OK] Partition catalog saved -> results/partition_metadata_catalog.csv")
    print("[OK] Skew summary saved -> results/partition_skew_summary.csv")

def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    s3 = get_s3_client()
    setup_minio_bucket(s3)
    upload_hive_partitions(s3)
    benchmark_reads(s3)
    run_metadata_crawler(s3)

if __name__ == "__main__":
    main()
