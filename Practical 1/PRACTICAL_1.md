# Practical 1: Data Engineering Lifecycle

## Aim / Problem Definition
To study, dissect, and map the complete end-to-end Data Engineering Lifecycle for an enterprise e-commerce platform across five core stages: Data Generation, Ingestion, Storage, Transformation, and Serving. Additionally, create architectural data flow diagrams (Level 0, Level 1, and Level 2) and document cross-cutting undercurrents including Security, Observability, and Data Privacy.

## Tools / Technologies
- Draw.io / Mermaid for Architectural & DFD diagrams
- Markdown for system manifesto and documentation
- Git for local version management

## Step-by-Step
1. **Identify Data Sources**: Map out transactional order databases, web clickstream events, inventory updates, and third-party APIs.
2. **Design Ingestion Layer**: Categorize data ingestion into real-time streaming (user clicks, payment events) and scheduled batch ingestion (daily inventory sync, catalog updates).
3. **Organize Storage Layer**: Store raw unstructured/semi-structured data in an object storage/data lake, and curated structured data in an analytical data warehouse.
4. **Transform Data**: Clean messy data, validate schemas, remove duplicates, and build dimensional models for reporting.
5. **Serve Analytics**: Expose processed metrics to business dashboards, machine learning models, and downstream microservices.
6. **Enforce Cross-Cutting Undercurrents**: Apply security (encryption, RBAC), observability (lineage, data quality monitoring, pipeline health), and privacy (GDPR compliance, PII masking).

## Output
- Level 0, Level 1, and Level 2 Data Flow Diagrams (DFD) visualizing data movement across systems.
- End-to-end Data Engineering Lifecycle diagram illustrating stages and undercurrents.
- Clear mapping of operational data conversion into business-ready analytical datasets.

## Key Questions

### 1. How do the technical demands of downstream serving layers directly influence ingestion and storage design decisions during the early generation phases?
The serving layer determines latency and query patterns. If downstream consumers require sub-second live dashboards, the ingestion layer must use streaming (like Kafka) and fast time-series storage. If downstream consumers only require weekly financial reports, cost-effective daily batch ingestion and columnar lake storage are chosen.

### 2. Differentiate between the broader data lifecycle and the technical data engineering lifecycle within an enterprise.
- **Data Lifecycle**: Covers the complete business journey of data from business creation, active utilization, retention policies, archival, to final legal deletion. It involves business users, compliance officers, and analysts.
- **Data Engineering Lifecycle**: Focuses purely on the technical movement and transformation of data: Generation, Ingestion, Storage, Transformation, and Serving. It is managed by data engineers and software architects.

### 3. Identify how the undercurrents of security and data observability should be enforced at each lifecycle boundary.
- **Data Generation**: Authenticate data producers, enforce source-level schemas, and log generation timestamps.
- **Data Ingestion**: Use TLS encryption in transit, rate-limit ingestion endpoints, and monitor ingestion latency and message drop rates.
- **Data Storage**: Apply AES-256 encryption at rest, enforce strict Role-Based Access Control (RBAC), and monitor storage volume skew and partition growth.
- **Data Transformation**: Mask sensitive PII before intermediate staging, log transformation failures, and track data lineage.
- **Data Serving**: Require API tokens, restrict column visibility by user role, monitor query execution times, and log audit trails.

## Supplementary Problem: Smart City IoT Traffic Sensor Platform
Map out the data engineering lifecycle for a smart city IoT traffic sensor platform, emphasizing challenges related to continuous real-time streaming data generation.

### Lifecycle Architecture:
1. **Data Generation**: Thousands of roadside vehicle counters, radar detectors, and smart traffic lights generate high-velocity telemetry (speed, count, occupancy) every 500ms.
2. **Data Ingestion**: Lightweight MQTT / HTTP gateways ingest edge sensor streams into distributed Kafka topics with geo-based partitions.
3. **Data Storage**: Raw sensor payloads land in object storage (MinIO/S3) partitioned by `city/date/hour`, while the latest 24-hour readings stay in Redis/TimescaleDB for fast lookup.
4. **Data Transformation**: Stream processors (or micro-batch jobs) filter noise, impute missing sensor readings, and calculate rolling 5-minute average vehicle speeds.
5. **Data Serving**: Live congestion alerts are pushed to traffic control operators and public commuter navigation APIs.
6. **Undercurrents & Challenges**:
   - **Continuous Stream Volume**: Sensors produce millions of events daily; network interruptions require local edge buffering.
   - **Out-of-Order Delivery**: Sensor signals arriving late due to cellular network lag must be handled using event-time watermarking.
   - **Observability**: Immediate dead-sensor detection through heartbeats and anomaly detection algorithms.

## Conclusion
The data engineering lifecycle successfully bridges raw operational event generation and high-value analytical serving. By planning storage and transformation according to downstream serving needs, and systematically enforcing security and observability undercurrents, data pipelines remain reliable, scalable, and secure.

## Screenshot List
- **Screenshot 1 – Data Engineering Lifecycle Diagram**: Shows the five stages and cross-cutting undercurrents.  
  *Where to place it*: Under Output section (`DataEngineering_LifeCycle.PNG`).
- **Screenshot 2 – E-Commerce Data Flow Diagram (DFD)**: Illustrates Level 0, 1, and 2 data flow for order and telemetry processing.  
  *Where to place it*: Under Output section (`DFD.png`).
