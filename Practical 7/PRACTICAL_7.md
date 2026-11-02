# Practical 7: Change Data Capture (CDC)

## Aim / Problem Definition
To implement a Change Data Capture (CDC) pipeline in PostgreSQL to capture all data mutations (INSERT, UPDATE, and DELETE) from an operational transactional inventory table into an append-only CDC ledger using PL/pgSQL database triggers. To build a Python replication loop that continuously replays change records into an analytical destination table, verify fault tolerance and recovery following an interrupted replication process, and implement version-based deduplication for out-of-order mutations.

## Tools / Technologies
- PostgreSQL (relational database engine)
- Python 3.13 (`psycopg2-binary`, `pandas`)
- PL/pgSQL (database triggers and audit functions)
- JSONB (structured before/after mutation payloads)

## Step-by-Step
1. **Initialize Schemas & Triggers**:
   - Create `operational_inventory` (operational source with `version` tracking).
   - Create `cdc_ledger` (immutable change log recording `op_type`, `payload_before`, `payload_after`, `version`, and `replicated` flag).
   - Create `analytical_inventory` (target table in analytics layer).
   - Attach PL/pgSQL trigger `trg_capture_inventory_cdc()` to `operational_inventory` to record all row changes automatically.
2. **Execute Transactional Mutations**: Run INSERT (5 items), UPDATE (3 items, incrementing version), and DELETE (1 item) operations. Verify that 9 distinct CDC events are logged in `cdc_ledger`.
3. **Replay Replication Loop**: Read unreplicated mutations in chronological sequence and apply them to `analytical_inventory`.
4. **Test Crash Interruption & Recovery**:
   - Interrupt the replication loop halfway (after processing 4 events).
   - Inspect uncommitted/unreplicated records remaining in the ledger.
   - Restart the replication loop and verify that processing resumes seamlessly without duplicate row creation.
5. **Supplementary Out-of-Order Version Deduplication**:
   - Inject an obsolete, out-of-order event (Version 1 arriving after Version 2 has already been applied).
   - Ensure the version-checked replay logic (`WHERE EXCLUDED.current_version >= target.current_version`) safely drops the outdated event, preventing state regression.
6. **Verify State Consistency**: Assert that the analytical table matches the operational source table with 100% precision.

## Output
- **CDC Ledger (`results/cdc_ledger_history.csv`)**: Full immutable audit trail recording all 9 mutation events (`INSERT`, `UPDATE`, `DELETE`) with exact timestamps and JSON payloads.
- **Analytical State (`results/analytical_replicated_state.csv`)**: Clean analytical mirror table verified to be 100% consistent with the operational inventory table.
- **Fault Recovery Verified**: Interrupted replication successfully recovered remaining events without duplicate insertion.
- **Version Deduplication Verified**: Obsolete out-of-order events rejected automatically.

## Key Questions

### 1. What are the key differences between log-based CDC and trigger-based CDC?
- **Trigger-Based CDC**: Implemented directly inside the database using PL/pgSQL triggers (`AFTER INSERT/UPDATE/DELETE`). It is easy to set up and works across all database types, but incurs overhead on transactional write throughput.
- **Log-Based CDC (e.g., Debezium, Postgres WAL)**: Reads changes directly from the database transaction write-ahead log (WAL) on disk. It introduces zero overhead on operational transactions and captures changes even if applications bypass standard SQL, making it the industry standard for high-throughput systems.

### 2. How does an append-only CDC ledger provide auditability and point-in-time recovery?
Because every INSERT, UPDATE, and DELETE is appended as an immutable record with before-and-after JSON state and timestamps, the ledger acts as a complete historical movie of the database. Point-in-time recovery can be achieved by replaying events up to a specific historical timestamp.

### 3. Why is version-based deduplication critical when replaying streaming CDC events?
Distributed message brokers and network retries can deliver change events out of order or multiple times (at-least-once delivery). If an older UPDATE (e.g. Version 1) is applied after a newer UPDATE (Version 2), the database state regresses to stale historical data. Version-based checks ensure only events with strictly higher version numbers update the target state.

## Supplementary Problem: Version-Based Deduplication for Out-of-Order Events
**Requirement**: Implement version-based deduplication for out-of-order changes.

**Implementation & Result**:
- Tested by injecting an obsolete Version 1 event for Item 101 when the analytical table was already at Version 2.
- The replication loop evaluated:
  ```sql
  UPDATE analytical_inventory
  SET ... WHERE item_id = %s AND %s >= current_version;
  ```
- **Result**: The outdated Version 1 event was safely evaluated and ignored. Current version remained at 2, and the correct current price ($74.99) was preserved.
- Output logged with `[PASS] Version protection verified: Obsolete version 1 event was safely discarded!`.

## Conclusion
Practical 7 demonstrated how Change Data Capture maintains synchronized analytical copies of operational databases. By pairing an immutable CDC audit ledger with an idempotent, version-aware replication loop, data engineering pipelines achieve resilience against crashes, network retries, and out-of-order message delivery.

## Screenshot List
- **Screenshot 1 – Database Initialization & Triggers**: Terminal output showing table creation and trigger establishment.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – CDC Ledger with Mutations**: Terminal output displaying captured INSERT, UPDATE, and DELETE events (`results/cdc_ledger_history.csv`).  
  *Where to place it*: Under Output section.
- **Screenshot 3 – Crash Interruption & Recovery Test**: Terminal output showing partial replication, simulated interruption, and successful recovery.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 4 – Supplementary Version Deduplication**: Terminal output confirming obsolete out-of-order event rejection.  
  *Where to place it*: Under Supplementary Problem section.
- **Screenshot 5 – Final Consistency Verification**: Terminal table showing identical operational and analytical table states.  
  *Where to place it*: Under Output section.
