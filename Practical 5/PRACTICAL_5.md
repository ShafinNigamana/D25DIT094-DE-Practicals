# Practical 5: Distributed Storage Systems

## Aim / Problem Definition
To implement and evaluate distributed object storage using Hive-style partitioning in an S3-compatible object store (SeaweedFS in Docker) using Python and Boto3. To organize a multi-year analytical dataset across hierarchical partitions (`year=YYYY/month=MM/region=REGION`), benchmark partition-pruned queries against full bucket scans to measure I/O and latency advantages, and implement a supplementary metadata crawler and partition balance/skew analyzer.

## Tools / Technologies
- SeaweedFS (S3-compatible object storage)
- Docker Desktop
- Python / Boto3
- Pandas / NumPy

## Step-by-Step
1. **Start S3-Compatible Storage Container**: Launch a local SeaweedFS S3-compatible object storage container using Docker:
   ```powershell
   docker run -d --name seaweedfs-s3 -p 8333:8333 -e "AWS_ACCESS_KEY_ID=admin" -e "AWS_SECRET_ACCESS_KEY=secret" chrislusf/seaweedfs
   ```
2. **Generate Partitioned Analytical Dataset**: Run `generate_dataset.py` to synthesize a multi-year transactional dataset structured as Hive partitions across 2024 and 2025, months 01–03, and regions (`north`, `south`, `east`, `west`).
3. **Connect and Upload via Boto3**: Run `minio_partition_storage.py` to connect to `http://localhost:8333` (credentials `admin` / `secret`), create the test bucket `de-warehouse-partitioned`, and upload all 24 partition files with S3 keys formatted as `year=2025/month=01/region=west/data.csv`.
4. **Benchmark Full Scan vs Partition Read**:
   - **Full Scan**: List and download all 24 objects across the entire bucket, measuring data transferred and query latency.
   - **Partition-Pruned Read**: Download only objects under the specific prefix `year=2025/month=01/region=west/` (target partition containing 5,000 rows, representing 6.67% of total records).
5. **Run Metadata Crawler & Skew Analyzer**: Crawl all object keys, calculate total bytes per partition, evaluate size standard deviation, and detect partition skew caused by volume imbalances.

## Output
- **Hive Partition Layout**: Uploaded 24 partition files organized under `year=YYYY/month=MM/region=REGION/`.
- **Read Benchmark (`results/read_benchmark.csv`)**:
  - **Full Bucket Scan**: 75,000 rows read across 24 partitions, 5435.14 KB data transferred, latency of **953.21 ms**.
  - **Partition-Pruned Read**: 5,000 rows read from target partition (`year=2025/month=01/region=west/`), 360.07 KB data transferred, latency of **41.70 ms**.
  - **Performance Advantage**: **22.86x faster** latency with **93.4% I/O reduction** (scanning only 6.67% of the total dataset rows).
- **Partition Catalog & Skew Report (`results/partition_metadata_catalog.csv` & `results/partition_skew_summary.csv`)**:
  - Total Partitions Cataloged: 24
  - Mean Partition Size: 226.46 KB
  - Standard Deviation: 89.42 KB
  - Coefficient of Variation: 0.395
  - Max / Min Skew Ratio: **3.34x** (Flags that the `west` region has significantly higher traffic volume).

## Key Questions

### 1. What are Hive-style partitions and why are they standard in cloud data lakes?
Hive-style partitions use directory naming conventions formatted as `key=value/` (e.g., `year=2025/month=01/region=west/`). Modern query engines (such as Spark, Presto, Trino, and DuckDB) inspect directory path names to infer column values without needing to open and parse the underlying files. This enables partition pruning, where irrelevant directories are skipped during query planning.

### 2. How does partition pruning reduce costs in cloud object stores like AWS S3?
Cloud providers charge for both data scanned (GET requests and data transfer) and compute time. When a query filters by partition keys (e.g. `WHERE year = 2025 AND region = 'west'`), the engine issues S3 list/get requests only for objects under that specific prefix, cutting down API request fees and network data transfer by up to 90+%.

### 3. What is partition skew and why is it dangerous?
Partition skew occurs when data is distributed unevenly across partitions (e.g., a major metro region having significantly more data than smaller regions). In distributed processing, the node or worker assigned to the oversized partition takes much longer to finish (the "straggler problem"), delaying the entire distributed pipeline.

## Supplementary Problem: Metadata Crawler and Skew Analyzer
**Requirement**: Implement the supplementary metadata crawler and calculate partition balance/skew.

**Implementation & Result**:
- The metadata crawler recursively scans all partition keys under `de-warehouse-partitioned` in S3-compatible storage.
- Computes mean partition size, standard deviation, coefficient of variation, and max/min ratio.
- **Result**: Successfully cataloged all 24 partitions into `results/partition_metadata_catalog.csv` and flagged high-volume regions (`west`, 360.07 KB) versus low-volume regions (`east`, 107.82 KB) with a **3.34x skew ratio** in `results/partition_skew_summary.csv`.

## Conclusion
Practical 5 demonstrated the core principles of distributed object storage using S3-compatible storage (SeaweedFS) and Hive-style partitioning. Structuring data with clear partition prefixes drastically accelerates analytical query performance through partition pruning (achieving a 22.86x speedup and 93.4% I/O reduction), while metadata crawlers ensure operational visibility over partition skew and storage distribution.

## Screenshot List
- **Screenshot 1 – Docker Container Running**: Terminal output of `docker ps` showing the `seaweedfs-s3` container running on port 8333.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – Benchmark Execution**: Terminal output of `minio_partition_storage.py` showing full scan vs partition-pruned read comparison.  
  *Where to place it*: Under Output section.
- **Screenshot 3 – Metadata Skew Report**: Contents of `results/partition_skew_summary.csv` displaying partition balance metrics.  
  *Where to place it*: Under Supplementary Problem section.
