# Practical 10: Batch and Streaming Transformations

## Aim / Problem Definition
To implement and compare batch and streaming transformations on out-of-order IoT sensor telemetry and device registry metadata. To perform batch filtering, cross-source enrichment, and rolling-window aggregations. In the streaming pipeline, to implement event-time processing with a dynamic watermark, evaluate how out-of-order and genuinely late-arriving events are processed, and implement a supplementary 5-minute per-user rolling fraud-volume detection check.

## Tools / Technologies
- Python 3.13
- Pandas (data manipulation and windowing)
- Python standard library (`datetime`, `timedelta`, `os`, `sys`, `shutil`)

## Step-by-Step
1. **Verify Environment**: Run `check_environment.py` to inspect runtime versions (Python 3.13.3, Java 1.8.0_481, PySpark availability).
2. **Generate IoT Workload**: Run `generate_iot_data.py` to synthesize:
   - Device registry metadata (`iot_metadata.csv`).
   - Out-of-order IoT telemetry containing corrupt rows, acceptable jitter, and a genuinely late record (`iot_telemetry.csv`).
   - Financial transactions for fraud checking (`user_transactions.csv`).
3. **Execute Batch Transformations**: Run `batch_transformations.py` to filter corrupt sensor entries (null temperature, negative battery), perform cross-source enrichment by joining with device metadata, and calculate rolling 10-second aggregations.
4. **Execute Streaming with Watermarks**: Run `streaming_watermark.py` with an allowed lateness threshold of 15 seconds. Stream events in physical arrival order:
   - Update `current_watermark = max_event_time - 15s`.
   - In-watermark out-of-order events (`EVT_0099_OOO`) are accepted into the window.
   - Genuinely late events (`EVT_9999_LATE`, 65 seconds late) arriving after the watermark closes are dropped and recorded in `results/late_dropped_events.csv`.
5. **Supplementary 5-Minute Rolling Fraud Detection**: Run `fraud_detection.py` using sliding event-time windows to identify users with $\ge 3$ transactions and $\ge \$1,000$ volume within any 5-minute window.

## Output
### Transformation and Streaming Results:
- **Batch Processing**:
  - Filtered out 2 corrupted records (null temperature and negative battery).
  - Enriched 50 clean events with device metadata (`model`, `location`, `firmware`).
  - Computed rolling 10-second average temperature and maximum vibration.
- **Streaming Watermark Processing**:
  - Accepted events (on-time & within watermark): **51 events**.
  - Dropped late events (exceeded watermark by 65s): **1 event (`EVT_9999_LATE`)**.
  - Quarantined late events saved to `results/late_dropped_events.csv`.
  - Full event audit log written to `logs/watermark_execution.log`.
- **Supplementary Fraud Detection**:
  - Detected 2 critical high-velocity volume spike alerts for `USER_B` (4 transactions totaling $1,650 within 3 minutes), logged to `results/fraud_alerts.csv`.

## Key Questions

### 1. What is the fundamental difference between processing time and event time in stream processing?
- **Processing Time**: The local system clock time of the server processing the event. It is simple but inaccurate if network lag or server delays occur.
- **Event Time**: The original timestamp when the event actually occurred on the client or IoT sensor device. Event time guarantees deterministic, reproducible analytics regardless of pipeline network delays.

### 2. How does a watermark prevent unbounded state memory growth in streaming engines?
In stream processing, window aggregations must keep state in memory waiting for potential late-arriving events. A watermark specifies a boundary: "no more events older than timestamp $T$ are expected." Once the watermark advances past the end of a window, the engine finalizes the aggregation, emits the result, and purges the window's state from memory, preventing out-of-memory errors.

### 3. What are the common architectural strategies for handling late-arriving data?
1. **Drop and Log**: Reject the event and log it to an audit trail (used when downstream data cannot be revised).
2. **Dead-Letter Queue / Quarantine**: Route late events to a dedicated storage path or quarantine queue for forensic analysis and manual reconciliation.
3. **Emit Updates / Retractions**: Allow a secondary grace period where late events update already-emitted window results in downstream analytical tables.

## Supplementary Problem: 5-Minute Per-User Rolling Fraud-Volume Check
**Requirement**: Implement the 5-minute per-user fraud-volume check using sliding window aggregations.

**Implementation & Result**:
- Evaluated sliding 5-minute event-time windows across user transactions.
- Criteria: Any user executing $\ge 3$ transactions AND exceeding $\$1,000$ total volume in a 5-minute sliding window triggers a critical alert.
- **Result**: Successfully flagged `USER_B` when they placed 4 rapid transactions within 3 minutes totaling $\$1,650$. Normal users (`USER_A` and `USER_C`) were not flagged.
- Alerts exported to `results/fraud_alerts.csv`.

## Conclusion
Practical 10 demonstrated how to process both batch and streaming workloads effectively. While batch transformations excel at bulk cleaning and metadata enrichment, streaming architectures with event-time watermarking are essential for handling network delays and identifying late-arriving data. Additionally, sliding window aggregations provide immediate detection of anomalous patterns such as payment fraud.

## Screenshot List
- **Screenshot 1 – Environment Check**: Terminal output showing Python and Java runtime checks (`check_environment.py`).  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – Batch Filtering & Enrichment**: Terminal output showing corrupt record filtering and rolling window calculations.  
  *Where to place it*: Under Output section.
- **Screenshot 3 – Streaming Watermark Processing**: Terminal output showing acceptance of in-watermark events and dropping of late event `EVT_9999_LATE`.  
  *Where to place it*: Under Output section.
- **Screenshot 4 – Watermark Audit Log**: Snippet of `logs/watermark_execution.log` displaying event arrival vs watermark evaluations.  
  *Where to place it*: Under Output section.
- **Screenshot 5 – Supplementary Fraud Detection Alert**: Terminal output showing flagged suspicious user activity (`results/fraud_alerts.csv`).  
  *Where to place it*: Under Supplementary Problem section.
