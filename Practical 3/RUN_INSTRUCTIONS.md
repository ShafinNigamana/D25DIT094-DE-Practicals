# How to Run Practical 3

## 1. Start Apache Kafka (KRaft mode)
Kafka is installed at `C:\kafka`.
Open a dedicated Command Prompt or PowerShell:
```cmd
cd C:\kafka
bin\windows\kafka-server-start.bat config\kraft\server.properties
```
*Wait until you see: `[KafkaServer id=1] started`.*

## 2. Open a New Terminal for Practical 3
Navigate to the Practical 3 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 3"
```

## 3. Verify Kafka Topic
Check or create the `telemetry` topic:
```cmd
cd C:\kafka
bin\windows\kafka-topics.bat --create --topic telemetry --bootstrap-server localhost:9092 --partitions 4 --replication-factor 1
bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092
```

## 4. Run the Producer & Consumer Test
Back in the Practical 3 terminal:
```powershell
# Test simple baseline producer
python producer.py

# Test baseline consumer
python consumer.py
```

## 5. Run the Automated Benchmark
Run the telemetry generator and compare streaming vs micro-batch across rates:
```powershell
python benchmark/run_benchmarks.py
```

## 6. Verify Output Files
Check the benchmark results and generated charts:
```powershell
dir results
```
- `results/benchmark_results.csv`
- `results/latency_comparison.png`
- `results/throughput_comparison.png`

## 7. Screenshots to Capture
1. Kafka server running terminal window.
2. `python benchmark/run_benchmarks.py` execution output.
3. `results/latency_comparison.png` chart.
4. `results/throughput_comparison.png` chart.
