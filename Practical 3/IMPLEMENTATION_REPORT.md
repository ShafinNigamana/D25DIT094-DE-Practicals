# Data Engineering Practical 3

## Implementation Report

**University:** CHARUSAT  
**Department:** Information Technology  
**Subject:** Data Engineering  
**Semester:** 5th  
**Subject Code:** ITUE301  
**Academic Year:** 2026-27 ODD  
**Platform:** Windows  
**Broker:** Apache Kafka in local KRaft mode  
**Bootstrap server:** `localhost:9092`

## 1. Aim

To design and compare two telemetry ingestion pipelines:

1. A periodic time-triggered micro-batch pipeline using Pandas.
2. A continuous low-latency event-streaming pipeline using Kafka-Python-NG.

Both pipelines use the same synthetic web application and server telemetry schema. The implementation records latency, throughput, processed-event counts, traffic-spike behavior, and provides a basis for fault-tolerance evaluation.

## 2. Work Completed

### Preserved baseline

The instructor-provided files were not replaced:

- `producer.py` sends three timestamped student records to `student_latency`.
- `consumer.py` consumes the records, safely handles invalid/plain-text messages, and calculates latency and throughput.

The baseline was syntax-validated successfully.

### Telemetry generation

`data/telemetry_generator.py` generates realistic randomized events containing:

- `event_id`
- `user_id`
- `event_type`
- `server_id`
- `cpu_percent`
- `memory_percent`
- `response_time_ms`
- `timestamp`
  The generator supports a configurable rate and duration, for example 100, 500, 1000, or 5000 events per second.

`data/telemetry_producer.py` sends these events to Kafka with configurable topic, broker, rate, duration, and starting event ID. Kafka producer acknowledgements are configured with `acks="all"` and retries enabled.

### Micro-batch pipeline

`batch/batch_processor.py` consumes telemetry from Kafka and collects records for a configurable interval, defaulting to five seconds. Each batch is converted to a Pandas DataFrame and reports:

- Event count
- Average and maximum CPU
- Average memory
- Average and maximum response time
- Average, minimum, and maximum event latency

Results are appended to `results/benchmark_results.csv` when the pipeline is executed.

### Real-time streaming pipeline

`streaming/streaming_consumer.py` consumes and processes each Kafka event as it arrives. It records:

- Event latency
- Average latency
- Minimum latency
- Maximum latency
- Number of processed events
- Measured throughput

It uses a Kafka consumer group and manual offset commits.

### Benchmarking and charts

`benchmark/benchmark.py` runs comparable batch and streaming trials for a list of input rates. It starts the consumer before the producer so the consumer can observe the workload.

`benchmark/plot_results.py` reads actual CSV measurements and creates:

- `results/latency_comparison.png`
- `results/throughput_comparison.png`

The chart script does not generate values when the benchmark CSV is missing or empty.
The benchmark was executed locally and generated the CSV and both PNG files.

### Traffic-spike support

`streaming/traffic_spike.py` provides a Windows command for increasing the number of topic partitions. The streaming consumer can be started multiple times with the same consumer-group name to demonstrate partition sharing and scale-out.

The topic was expanded from one partition to four partitions. A measured 1000 events/sec spike for three seconds produced and processed 3000 events in both pipelines. The spike CSV recorded batch average latency of 1246.165 ms and streaming average latency of 3.739 ms.

The expected demonstration is:

```text
One partition  -> at most one active consumer in a group
Four partitions -> up to four active consumers in a group
```

## 3. Folder Structure

Generated Python cache folders are omitted from this documentation tree.

```text
DE_P3/
|
|-- producer.py                         Preserved baseline producer
|-- consumer.py                         Preserved baseline consumer
|-- Pr-3_English.docx                   Instructor practical document
|-- Kafka KRaft Log Directory Error.docx Instructor Kafka notes
|-- IMPLEMENTATION_REPORT.md            This implementation report
|
|-- data/
|   |-- telemetry_generator.py          Synthetic telemetry generator
|   `-- telemetry_producer.py            Kafka telemetry producer
|
|-- batch/
|   `-- batch_processor.py               Pandas micro-batch consumer
|
|-- streaming/
|   |-- streaming_consumer.py            Real-time Kafka consumer
|   `-- traffic_spike.py                  Partition scaling helper
|
|-- benchmark/
|   |-- benchmark.py                     Experiment runner
|   `-- plot_results.py                  Chart generator
|
`-- results/                             Created after experiments
    |-- benchmark_results.csv             Measured benchmark rows
    |-- latency_comparison.png            Latency chart
    `-- throughput_comparison.png        Throughput chart
```

## 4. Kafka Setup Commands

These commands assume the Kafka installation directory is the current directory. If Kafka is installed elsewhere, run them from that Kafka directory or use its absolute path.

Create the telemetry topic with one partition for the initial demonstration:

```powershell
bin\windows\kafka-topics.bat --create --topic telemetry --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

Check the topic:

```powershell
bin\windows\kafka-topics.bat --describe --topic telemetry --bootstrap-server localhost:9092
```

For the traffic-spike experiment, increase the topic to four partitions. Kafka partition counts can be increased, not decreased:

```powershell
bin\windows\kafka-topics.bat --alter --topic telemetry --bootstrap-server localhost:9092 --partitions 4
```

## 5. Demonstration Commands

All commands below are run from:

```powershell
C:\Users\shafi\OneDrive\Scans\Desktop\DE_P3
```

### Telemetry generator smoke test

```powershell
python data\telemetry_generator.py --rate 10 --duration 5 --output telemetry.jsonl
```

### Real-time streaming test

Terminal 1:

```powershell
python streaming\streaming_consumer.py --topic telemetry --expected-events 50 --timeout 30 --offset-reset latest --input-rate 10
```

Terminal 2:

```powershell
python data\telemetry_producer.py --topic telemetry --rate 10 --duration 5
```

### Micro-batch test

Terminal 1:

```powershell
python batch\batch_processor.py --topic telemetry --expected-events 50 --timeout 30 --batch-interval 5 --offset-reset latest --input-rate 10
```

Terminal 2:

```powershell
python data\telemetry_producer.py --topic telemetry --rate 10 --duration 5
```

### Full benchmark

Ensure the `telemetry` topic exists and Kafka is running, then execute:

```powershell
python benchmark\benchmark.py --rates 100 500 1000 --duration 10 --batch-interval 5 --clear-results
```

For a smaller computer, use:

```powershell
python benchmark\benchmark.py --rates 10 50 100 --duration 5 --batch-interval 3 --clear-results
```

Generate charts after the benchmark:

```powershell
python benchmark\plot_results.py
```

## 6. Benchmark CSV Format

The implementation writes these columns:

```text
pipeline,input_rate,events_generated,events_processed,average_latency_ms,minimum_latency_ms,maximum_latency_ms,throughput_events_per_sec
```

All values in the CSV come from actual execution. The completed five-second benchmark used requested rates of 100, 500, and 1000 events/sec:

| Pipeline  | Input rate | Generated | Processed | Average latency (ms) | Maximum latency (ms) | Throughput (events/sec) |
| --------- | ---------: | --------: | --------: | -------------------: | -------------------: | ----------------------: |
| Batch     |        100 |       500 |       500 |             1136.615 |             2167.871 |                  54.331 |
| Streaming |        100 |       500 |       500 |                3.078 |               24.211 |                  55.576 |
| Batch     |        500 |      2500 |      2500 |             1146.603 |             2202.749 |                 270.723 |
| Streaming |        500 |      2500 |      2500 |                2.577 |                9.346 |                 276.627 |
| Batch     |       1000 |      5000 |      5000 |             1151.011 |             2201.256 |                 546.612 |
| Streaming |       1000 |      5000 |      5000 |                3.499 |               21.123 |                 557.345 |

## 7. Traffic-Spike Experiment

1. Run the initial test with one topic partition and one consumer.
2. Record the processed event count and throughput.
3. Increase the topic to four partitions:

```powershell
python streaming\traffic_spike.py --topic telemetry --partitions 4
```

4. Start multiple consumers with the same group ID, for example `spike-group`, in separate terminals:

```powershell
python streaming\streaming_consumer.py --topic telemetry --group spike-group --timeout 30 --input-rate 1000
```

5. Start the producer with a spike workload:

```powershell
python data\telemetry_producer.py --topic telemetry --rate 1000 --duration 10
```

Consumers in the same group share partitions. Adding consumers beyond the partition count does not provide additional active partition parallelism. Adding partitions allows more consumers in that group to process concurrently. In this environment, grouped kafka-python-ng polling failed with an `Invalid file descriptor` error, so automated measurements used explicit manual assignment. Group mode remains available for diagnosis and should be verified separately for the final scale-out demonstration.

## 8. Fault-Tolerance Experiment Status

A single broker with replication factor one cannot demonstrate broker failover. If broker 1 stops, there is no replica to become a new leader, so continued service and zero-loss behavior must not be claimed.

The current implementation does not claim that a multi-broker replicated KRaft cluster has been created or verified. A valid fault-tolerance experiment requires three separately configured local brokers, separate node IDs, ports, log directories, and a replicated topic with replication factor three. The experiment is therefore pending reliable local cluster setup and runtime verification.

For a verified multi-broker test, record:

- Stopped broker ID
- Partition leader before failure
- New leader after failure
- Producer and consumer behavior
- Processed and missing event counts
- Recovery time

## 9. Required Measurements

For every workload, compare batch and streaming using the same requested rate and duration:

- Data delivery or processing latency
- Processing throughput
- Events generated
- Events processed
- Behavior during traffic spikes
- Resource usage if added later
- Fault-tolerance behavior only when replication is actually configured

The latency formula is:

```text
latency_ms = (processing_time - event_timestamp) * 1000
```

The throughput formula is:

```text
throughput = processed_events / elapsed_processing_time
```

## 10. Expected Observations

These are expected engineering observations, not measured results:

- Streaming normally provides lower event latency because events are processed individually.
- Micro-batch processing adds waiting time until the next batch interval but simplifies aggregation and can process records efficiently in groups.
- Kafka partitions provide parallelism; consumer count alone does not increase parallelism when there are too few partitions.
- Higher input rates can increase queueing and latency when producer, broker, network, or consumer capacity is exceeded.
- Replication is required for a broker failure to be recoverable without losing the only copy of a partition.

## 11. Answers to Analysis Questions

### Question 1

Micro-batch processing is a better operational balance when the application can tolerate seconds of delay, needs periodic aggregation, has moderate or bursty workloads, and benefits from simpler deployment and debugging. It usually has fewer continuously running coordination concerns than a true real-time system. Real-time streaming is preferable when each event must trigger action immediately, such as security alerts or transactional synchronization.

### Question 2

A broker cluster maintains delivery guarantees by storing replicated partition logs on multiple brokers. Producers can require acknowledgements from all in-sync replicas, and consumers track committed offsets. If a leader disconnects, the controller elects an eligible replica as the new leader. Producers retry failed sends and consumers resume from their committed offsets. These guarantees depend on correct replication, producer acknowledgement settings, in-sync replica configuration, and appropriate offset management. A single broker with replication factor one provides no failover guarantee.

### Question 3

Bulk file compression generally reduces network bandwidth and storage usage by compressing many records together, but it adds batch waiting time and CPU work during compression and decompression. Individual event serialization sends data quickly and supports low latency, but each event carries serialization and protocol overhead, causing more CPU operations and potentially more network packets. Micro-batches favor compression efficiency and throughput; individual streaming events favor responsiveness and low delivery latency.

## 12. Limitations

- The current local Kafka setup is single-broker and replication factor one, so broker failover is not yet demonstrated.
- Results and charts were generated from actual local Kafka benchmark execution.
- The producer uses a timing loop and therefore reports an approximate requested rate; actual rates should be taken from execution output and CSV results.
- CPU and memory monitoring are not currently included because the primary latency and throughput measurements are implemented first.
- Kafka partition expansion redistributes future records but does not reorganize existing records.
- A local Windows setup is suitable for demonstration but does not represent a production cluster.
- Kafka's Windows launcher required `KAFKA_HEAP_OPTS` because the bundled script calls the unavailable `wmic` utility on this system.
- The installed kafka-python-ng grouped consumer encountered `Invalid file descriptor`; manual partition assignment was used for reliable benchmark measurements.

## 13. Validation Performed

The following validation passed:

```powershell
python -m py_compile data\telemetry_generator.py data\telemetry_producer.py batch\batch_processor.py streaming\streaming_consumer.py benchmark\benchmark.py benchmark\plot_results.py streaming\traffic_spike.py
```

The telemetry generator smoke test produced timestamped telemetry events, and all practical modules imported successfully.

## 14. Conclusion

The project now contains a preserved Kafka baseline and an extended telemetry practical implementation covering synthetic event generation, Kafka production, Pandas micro-batching, real-time streaming, benchmark recording, chart generation, and partition-scaling support. Runtime benchmark values, comparative charts, and broker-failure observations must be generated by executing the experiments on the local Kafka installation.
