# How to Run Practical 5

## 1. Start Docker Container (SeaweedFS S3-Compatible Server)
Ensure Docker Desktop is running on Windows. Start the SeaweedFS S3 server container:
```powershell
docker run -d --name seaweedfs-s3 -p 8333:8333 -e "AWS_ACCESS_KEY_ID=admin" -e "AWS_SECRET_ACCESS_KEY=secret" chrislusf/seaweedfs
```
Verify the container is active:
```powershell
docker ps
```
*The server provides a local S3-compatible endpoint at `http://localhost:8333` with access key `admin` and secret key `secret`.*

## 2. Open Terminal
Navigate to the Practical 5 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 5"
```

## 3. Generate Partitioned Dataset
Run the data generator to create the 24 Hive-style partition folders:
```powershell
python generate_dataset.py
```

## 4. Run S3 Partition Storage & Benchmark
Execute the upload, benchmark, and metadata crawler:
```powershell
python minio_partition_storage.py
```
*(The script uses default endpoint `http://localhost:8333` and credentials `admin` / `secret` directly without needing manual environment variables.)*

## 5. Verify Output Files
Verify the generated benchmark and metadata outputs:
```powershell
dir results
type results\read_benchmark.csv
type results\partition_skew_summary.csv
```
You will find:
- `results/read_benchmark.csv` (Full scan vs partition-pruned latency & I/O)
- `results/partition_metadata_catalog.csv` (Catalog of all 24 partitions)
- `results/partition_skew_summary.csv` (Partition balance and skew metrics)

## 6. Screenshots to Capture
1. Terminal output of `docker ps` showing `seaweedfs-s3` running.
2. Terminal output of `python minio_partition_storage.py` (showing benchmark execution & skew analysis).
3. Contents of `results/partition_skew_summary.csv`.
