# How to Run Practical 6

## 1. MANUAL SETUP: Ensure MinIO is Running
Ensure the MinIO Docker container is running (from Practical 5):
```powershell
docker ps
```
If not running, start it:
```powershell
docker run -d --name minio-server -p 9000:9000 -p 9001:9001 -e "MINIO_ROOT_USER=minioadmin" -e "MINIO_ROOT_PASSWORD=minioadmin" quay.io/minio/minio server /data --console-address ":9001"
```

## 2. Open Terminal
Navigate to the Practical 6 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 6"
```

## 3. Run Storage Lifecycle Manager
This script creates the test bucket, applies `lifecycle_policy.json`, uploads objects with simulated age profiles, identifies objects inactive for $> 90$ days, tags/demotes them to Cold tier, and calculates the cost/benefit savings:
```powershell
python storage_lifecycle_manager.py
```

## 4. Verify Output Files
```powershell
dir results
type results\lifecycle_evaluation.csv
type results\cost_benefit_comparison.csv
```
You will find:
- `lifecycle_policy.json`
- `results/lifecycle_evaluation.csv`
- `results/cost_benefit_comparison.csv`

## 5. Screenshots to Capture
1. Contents of `lifecycle_policy.json`.
2. Terminal output of `python storage_lifecycle_manager.py` (showing 90-day inactivity detection and cost comparison).
3. MinIO Web Console at `http://localhost:9001` showing bucket `de-lifecycle-test`.
