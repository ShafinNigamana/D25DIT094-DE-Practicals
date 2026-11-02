# Reusable Storage Module – Practical 5

## 1. Purpose of the Storage Module
This module fulfills the university Practical 5 post-lab requirement:
> *"Save your container compose setups, bucket partition mapping rules, and verification search scripts into a reusable storage module within your lab repository."*

It encapsulates:
1. Declarative Docker Compose definition for running S3-compatible storage.
2. Formal Hive partition mapping documentation.
3. A lightweight verification script (`verify_storage.py`) to validate bucket health and partition availability.

---

## 2. Starting Storage with Docker Compose
To start the S3-compatible object storage server using Docker Compose:

```powershell
# From the Practical 5 directory:
docker compose up -d
```

This brings up `seaweedfs-s3` on port `8333` with access key `admin` and secret key `secret`.

---

## 3. How to Run `verify_storage.py`
From the `Practical 5` directory:

```powershell
python storage_module/verify_storage.py
```

---

## 4. What Verification Checks
`verify_storage.py` performs 3 core health checks against the S3 endpoint:
1. **Bucket Accessibility**: Confirms that bucket `de-warehouse-partitioned` exists and accepts Boto3 requests.
2. **Object & Partition Inventory**: Counts stored objects (ensuring all 24 Hive partitions are present) and reports total storage bytes.
3. **Partition Pruning Target Check**: Verifies that prefix `year=2025/month=01/region=west/` exists with valid object data.

Outputs clear `[OK]` status messages and exits with code `0` on success.

---

## 5. Relationship with `minio_partition_storage.py`
- `minio_partition_storage.py` is the **main benchmark script** that uploads the 75,000 generated records, measures full scan vs partition-pruned read latency, and runs statistical skew analysis.
- `storage_module/verify_storage.py` is a **lightweight, non-destructive verification tool** that checks storage state without re-uploading datasets or re-running full latency benchmarks.
