# Practical 3: Batch vs Streaming Data Ingestion

## Aim / Problem Definition
To design and implement a real-time data processing pipeline using Apache Kafka. The practical compares continuous streaming and periodic micro-batch processing for server and web application telemetry data by measuring processing latency and throughput across different event generation rates (10, 50, 100, and 1000 events/sec).

## Tools / Technologies
- Apache Kafka (KRaft mode, local cluster on `localhost:9092`)
- Python 3.13 (`kafka-python-ng`)
- Pandas (micro-batch aggregations)
- Matplotlib (performance benchmarking graphs)

## Step-by-Step
1. **Start Apache Kafka**: Start the Kafka broker in KRaft mode using `config\kraft\server.properties`.
2. **Create Telemetry Topic**: Create a partitioned Kafka topic named `telemetry` (4 partitions, replication factor 1) to enable scalable parallel message ingestion.
3. **Generate Telemetry Workload**: Use `data/telemetry_producer.py` to stream realistic randomized server events (CPU, memory, response time, latency timestamp) at varying rates.
4. **Run Continuous Streaming Pipeline**: Ingest events record-by-record via `streaming/streaming_processor.py` to achieve immediate sub-5ms processing.
5. **Run Micro-Batch Pipeline**: Buffer incoming events into 5-second tumbling windows using `batch/batch_processor.py`, computing summary statistics over each window.
6. **Benchmark and Analyze**: Execute `benchmark/run_benchmarks.py` across different input rates, collect latency and throughput metrics in `results/benchmark_results.csv`, and plot comparison curves.

## Output
- **Benchmark CSV (`results/benchmark_results.csv`)**: Contains measured latency and throughput for batch and streaming at 10, 50, 100, and 1000 events/sec.
- **Latency Chart (`results/latency_comparison.png`)**: Shows that streaming consistently maintains 1.9–2.9 ms latency, while micro-batch latency averages 1700–2700 ms due to window accumulation.
- **Throughput Chart (`results/throughput_comparison.png`)**: Shows scaling performance as message volume increases up to 5,000 events.

## Key Questions

### 1. What is the difference between streaming and micro-batch processing?
- **Streaming**: Processes each incoming record immediately upon arrival (event-by-event). It provides ultra-low latency (milliseconds) and is ideal for real-time alerting, fraud detection, and live monitoring.
- **Micro-Batch**: Buffers incoming records into small time windows (e.g., 2–10 seconds) or record count thresholds before processing them together. It introduces latency proportional to the window duration but optimizes compute throughput and bulk database writes.

### 2. How does Apache Kafka support real-time data processing?
Apache Kafka functions as a distributed, append-only commit log. It decouples high-speed data producers from multiple downstream consumers, allows horizontal scaling through topic partitioning, retains data durably on disk, and supports offset tracking so consumers can process messages sequentially at their own pace without data loss.

### 3. Which performance parameters are used to compare the two pipelines?
1. **Average Processing Latency**: Time elapsed from message creation by the producer to successful processing by the consumer.
2. **Min/Max Latency**: Range of latency variation showing jitter and buffering delays.
3. **Throughput (events/sec)**: Rate of successfully processed records per second.
4. **Resource Consumption**: Memory and CPU utilization during batch vs continuous execution.

## Supplementary Problem: Dynamic Scaling & Spike Analysis
**Requirement**: Develop and evaluate a Kafka-based telemetry processing system that compares streaming and micro-batch processing at different input rates and identifies the suitable processing approach for low-latency applications.

**Implementation & Result**:
- Benchmarked at 10, 50, 100, and 1000 events/sec.
- **Result**: Streaming latency stayed virtually constant (average 1.97 ms at 100 eps, 2.89 ms at 1000 eps). Micro-batch latency remained bounded by the 3–5 second collection window (average ~1700–2700 ms).
- **Conclusion**: Continuous streaming is strictly required for sub-second operational monitoring, while micro-batching is superior for high-volume analytical rollups where seconds of delay are acceptable.

## Conclusion
Practical 3 successfully demonstrated the core trade-offs between stream processing and micro-batching using Apache Kafka. Streaming provides near-instantaneous event delivery (under 3 ms), making it indispensable for live mission-critical telemetry, whereas micro-batching achieves higher batch efficiencies for heavy analytical queries.

## Screenshot List
- **Screenshot 1 – Kafka Server & Topic Creation**: Verification of the Kafka KRaft broker and `telemetry` topic list.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – Telemetry Producer Execution**: Terminal output showing 500/5000 events generated at designated rates.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 3 – Streaming vs Batch Consumer Output**: Side-by-side terminal output showing latency comparisons.  
  *Where to place it*: Under Output section.
- **Screenshot 4 – Latency Comparison Chart**: Graph showing latency across input rates (`results/latency_comparison.png`).  
  *Where to place it*: Under Output section.
- **Screenshot 5 – Throughput Comparison Chart**: Graph showing throughput across input rates (`results/throughput_comparison.png`).  
  *Where to place it*: Under Output section.
