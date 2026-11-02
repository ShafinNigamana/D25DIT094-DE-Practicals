# How to Run Practical 10

## 1. Open Terminal
Navigate to Practical 10 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 10"
```

## 2. Run the Complete Pipeline
Run all stages (Environment check, data generation, batch transformations, streaming watermarks, and fraud detection):
```powershell
python run_all.py
```

*Or run individual steps:*
```powershell
# Step 1: Environment check
python check_environment.py

# Step 2: Data generation
python generate_iot_data.py

# Step 3: Batch filtering and enrichment
python batch_transformations.py

# Step 4: Streaming watermark processing
python streaming_watermark.py

# Step 5: Supplementary fraud check
python fraud_detection.py
```

## 3. Verify Output Files
Check generated data, results, and logs:
```powershell
dir results
dir logs
type results\fraud_alerts.csv
type results\late_dropped_events.csv
```
You will find:
- `results/batch_enriched_telemetry.csv`
- `results/batch_rolling_summary.csv`
- `results/streaming_accepted_events.csv`
- `results/late_dropped_events.csv`
- `results/fraud_alerts.csv`
- `logs/watermark_execution.log`

## 4. Screenshots to Capture
1. Terminal output of `python check_environment.py`.
2. Terminal output of `python batch_transformations.py`.
3. Terminal output of `python streaming_watermark.py` (showing late event dropped).
4. Terminal output of `python fraud_detection.py` (showing fraud alerts).
