"""
cdc_pipeline.py
Practical 7: Change Data Capture (CDC) with PostgreSQL
Implements trigger-based CDC ledger capturing INSERT/UPDATE/DELETE,
Python replication/replay loop into analytical tables, fault-interruption recovery,
and supplementary version-based deduplication for out-of-order events.
"""

import os
import sys
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", 5432))
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASS = os.getenv("PG_PASS", "postgres")
PG_DB   = os.getenv("PG_DB", "postgres")

def get_connection():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASS,
        dbname=PG_DB,
        connect_timeout=3
    )

def setup_schema(conn):
    print("\n1. Initializing Operational, CDC Ledger, and Analytical Tables...")
    cursor = conn.cursor()
    
    # 1. Operational Inventory Table
    cursor.execute("""
    DROP TABLE IF EXISTS cdc_ledger CASCADE;
    DROP TABLE IF EXISTS analytical_inventory CASCADE;
    DROP TABLE IF EXISTS operational_inventory CASCADE;

    CREATE TABLE operational_inventory (
        item_id INT PRIMARY KEY,
        item_name VARCHAR(100) NOT NULL,
        quantity INT NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        version INT NOT NULL DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. CDC Audit Ledger Table
    CREATE TABLE cdc_ledger (
        cdc_id SERIAL PRIMARY KEY,
        op_type VARCHAR(10) NOT NULL,
        item_id INT NOT NULL,
        payload_before JSONB,
        payload_after JSONB,
        version INT NOT NULL,
        event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        replicated BOOLEAN DEFAULT FALSE
    );

    -- 3. Analytical Destination Table
    CREATE TABLE analytical_inventory (
        item_id INT PRIMARY KEY,
        item_name VARCHAR(100) NOT NULL,
        quantity INT NOT NULL,
        price NUMERIC(10, 2) NOT NULL,
        current_version INT NOT NULL,
        last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 4. PL/pgSQL CDC Trigger Function
    cursor.execute("""
    CREATE OR REPLACE FUNCTION trg_capture_inventory_cdc()
    RETURNS TRIGGER AS $$
    BEGIN
        IF (TG_OP = 'INSERT') THEN
            INSERT INTO cdc_ledger (op_type, item_id, payload_before, payload_after, version)
            VALUES ('INSERT', NEW.item_id, NULL, row_to_json(NEW)::jsonb, NEW.version);
            RETURN NEW;
        ELSIF (TG_OP = 'UPDATE') THEN
            INSERT INTO cdc_ledger (op_type, item_id, payload_before, payload_after, version)
            VALUES ('UPDATE', NEW.item_id, row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb, NEW.version);
            RETURN NEW;
        ELSIF (TG_OP = 'DELETE') THEN
            INSERT INTO cdc_ledger (op_type, item_id, payload_before, payload_after, version)
            VALUES ('DELETE', OLD.item_id, row_to_json(OLD)::jsonb, NULL, OLD.version);
            RETURN OLD;
        END IF;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER inventory_cdc_trigger
    AFTER INSERT OR UPDATE OR DELETE ON operational_inventory
    FOR EACH ROW EXECUTE FUNCTION trg_capture_inventory_cdc();
    """)
    
    conn.commit()
    print("[OK] Operational, CDC Ledger, and Analytical tables initialized with triggers.")

def generate_mutations(conn):
    print("\n2. Executing Operational Mutations (INSERT, UPDATE, DELETE)...")
    cursor = conn.cursor()
    
    # Phase A: INSERT 5 items
    cursor.execute("""
    INSERT INTO operational_inventory (item_id, item_name, quantity, price, version) VALUES
    (101, 'Mechanical Keyboard', 50, 79.99, 1),
    (102, 'Wireless Mouse', 120, 34.50, 1),
    (103, 'Ultra-wide Monitor', 25, 429.00, 1),
    (104, 'USB-C Docking Hub', 80, 59.99, 1),
    (105, 'Webcam 4K', 40, 99.00, 1);
    """)
    conn.commit()
    print("[OK] Phase A: Inserted 5 items.")
    
    # Phase B: UPDATE 3 items
    cursor.execute("""
    UPDATE operational_inventory 
    SET quantity = 35, price = 74.99, version = version + 1, updated_at = CURRENT_TIMESTAMP
    WHERE item_id = 101;

    UPDATE operational_inventory 
    SET quantity = 110, version = version + 1, updated_at = CURRENT_TIMESTAMP
    WHERE item_id = 102;

    UPDATE operational_inventory 
    SET price = 399.99, version = version + 1, updated_at = CURRENT_TIMESTAMP
    WHERE item_id = 103;
    """)
    conn.commit()
    print("[OK] Phase B: Updated 3 items (incremented version).")
    
    # Phase C: DELETE 1 item (Item 104)
    cursor.execute("DELETE FROM operational_inventory WHERE item_id = 104;")
    conn.commit()
    print("[OK] Phase C: Deleted item 104.")
    
    # Check CDC ledger
    cursor.execute("SELECT cdc_id, op_type, item_id, version, event_time FROM cdc_ledger ORDER BY cdc_id;")
    records = cursor.fetchall()
    print(f"\n[OK] CDC Ledger captured {len(records)} mutations automatically via PL/pgSQL trigger:")
    for r in records:
        print(f"  CDC #{r[0]}: [{r[1]:<6}] Item={r[2]} Version={r[3]} Time={r[4]}")

def replay_cdc_loop(conn, limit=None):
    """Replays pending CDC events into the analytical destination table with idempotency."""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    sql = "SELECT * FROM cdc_ledger WHERE replicated = FALSE ORDER BY cdc_id ASC"
    if limit:
        sql += f" LIMIT {limit}"
    cursor.execute(sql)
    events = cursor.fetchall()
    
    replayed_count = 0
    with conn.cursor() as apply_cursor:
        for ev in events:
            cdc_id = ev["cdc_id"]
            op = ev["op_type"]
            item_id = ev["item_id"]
            ver = ev["version"]
            payload = ev["payload_after"]
            
            if op == "INSERT":
                apply_cursor.execute("""
                INSERT INTO analytical_inventory (item_id, item_name, quantity, price, current_version, last_synced_at)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (item_id) DO UPDATE 
                SET item_name = EXCLUDED.item_name,
                    quantity = EXCLUDED.quantity,
                    price = EXCLUDED.price,
                    current_version = EXCLUDED.current_version,
                    last_synced_at = CURRENT_TIMESTAMP
                WHERE EXCLUDED.current_version >= analytical_inventory.current_version;
                """, (item_id, payload["item_name"], payload["quantity"], payload["price"], ver))
                
            elif op == "UPDATE":
                apply_cursor.execute("""
                UPDATE analytical_inventory
                SET item_name = %s,
                    quantity = %s,
                    price = %s,
                    current_version = %s,
                    last_synced_at = CURRENT_TIMESTAMP
                WHERE item_id = %s AND %s >= current_version;
                """, (payload["item_name"], payload["quantity"], payload["price"], ver, item_id, ver))
                
            elif op == "DELETE":
                apply_cursor.execute("DELETE FROM analytical_inventory WHERE item_id = %s;", (item_id,))
                
            # Mark as replicated
            apply_cursor.execute("UPDATE cdc_ledger SET replicated = TRUE WHERE cdc_id = %s;", (cdc_id,))
            replayed_count += 1
            
        conn.commit()
    return replayed_count

def test_interruption_recovery(conn):
    print("\n--------------------------------------------------")
    print("STEP 3: SIMULATING CRASH / INTERRUPTION & RECOVERY")
    print("--------------------------------------------------")
    
    # 1. Partial Replay (Simulate crash after 4 events)
    print("Simulating crash after processing first 4 events...")
    partial_replayed = replay_cdc_loop(conn, limit=4)
    print(f"Partial run processed: {partial_replayed} events.")
    
    # Check pending events
    with conn.cursor() as c:
        c.execute("SELECT COUNT(*) FROM cdc_ledger WHERE replicated = FALSE;")
        unreplicated = c.fetchone()[0]
    print(f"Unreplicated events remaining after simulated interruption: {unreplicated}")
    
    # 2. Recover and Resume
    print("\nResuming replication loop (Crash Recovery)...")
    resumed_replayed = replay_cdc_loop(conn)
    print(f"[OK] Recovery successful: Processed remaining {resumed_replayed} events.")
    
    with conn.cursor() as c:
        c.execute("SELECT COUNT(*) FROM cdc_ledger WHERE replicated = FALSE;")
        remaining = c.fetchone()[0]
    print(f"[OK] Remaining unreplicated events: {remaining}")

def test_out_of_order_deduplication(conn):
    print("\n--------------------------------------------------")
    print("SUPPLEMENTARY PROBLEM: VERSION-BASED DEDUPLICATION")
    print("--------------------------------------------------")
    
    with conn.cursor() as c:
        # Check current analytical state for Item 101 (version is 2, price is 74.99)
        c.execute("SELECT item_id, item_name, quantity, price, current_version FROM analytical_inventory WHERE item_id = 101;")
        current_state = c.fetchone()
        print(f"Current Analytical State for Item 101: Version={current_state[4]}, Price=${current_state[3]}")
        
        # Inject an obsolete out-of-order event (version 1 arriving AFTER version 2)
        print("\nInjecting obsolete out-of-order event (Version 1 arriving late)...")
        obsolete_event = {
            "op_type": "UPDATE",
            "item_id": 101,
            "version": 1,
            "payload_after": json.dumps({"item_id": 101, "item_name": "Mechanical Keyboard", "quantity": 50, "price": 79.99, "version": 1})
        }
        c.execute("""
        INSERT INTO cdc_ledger (op_type, item_id, payload_after, version, replicated)
        VALUES (%s, %s, %s::jsonb, %s, FALSE);
        """, (obsolete_event["op_type"], obsolete_event["item_id"], obsolete_event["payload_after"], obsolete_event["version"]))
        conn.commit()
        
    # Replay
    print("Running replication loop with version protection...")
    replay_cdc_loop(conn)
    
    with conn.cursor() as c:
        c.execute("SELECT item_id, item_name, quantity, price, current_version FROM analytical_inventory WHERE item_id = 101;")
        final_state = c.fetchone()
        print(f"Final Analytical State for Item 101: Version={final_state[4]}, Price=${final_state[3]}")
        
    if final_state[4] == 2 and float(final_state[3]) == 74.99:
        print("[PASS] Version protection verified: Obsolete version 1 event was safely discarded!")
    else:
        print("[FAIL] State regressed to obsolete version!")

def verify_consistency(conn):
    print("\n--------------------------------------------------")
    print("STATE VERIFICATION: OPERATIONAL VS ANALYTICAL")
    print("--------------------------------------------------")
    
    df_op = pd.read_sql_query("SELECT item_id, item_name, quantity, price, version FROM operational_inventory ORDER BY item_id;", conn)
    df_an = pd.read_sql_query("SELECT item_id, item_name, quantity, price, current_version AS version FROM analytical_inventory ORDER BY item_id;", conn)
    
    print("\nOperational Inventory Table:")
    print(df_op.to_string(index=False))
    print("\nAnalytical Replicated Table:")
    print(df_an.to_string(index=False))
    
    # Assert equality
    assert len(df_op) == len(df_an), "Row counts mismatch!"
    for i in range(len(df_op)):
        assert df_op.iloc[i]["item_id"] == df_an.iloc[i]["item_id"]
        assert df_op.iloc[i]["quantity"] == df_an.iloc[i]["quantity"]
        assert df_op.iloc[i]["price"] == df_an.iloc[i]["price"]
        assert df_op.iloc[i]["version"] == df_an.iloc[i]["version"]
        
    print("\n[OK] Verification Success: Operational and Analytical tables are 100% IDENTICAL.")
    
    # Export results
    os.makedirs("results", exist_ok=True)
    df_an.to_csv("results/analytical_replicated_state.csv", index=False)
    
    # Export CDC ledger log
    df_ledger = pd.read_sql_query("SELECT cdc_id, op_type, item_id, version, replicated, event_time FROM cdc_ledger ORDER BY cdc_id;", conn)
    df_ledger.to_csv("results/cdc_ledger_history.csv", index=False)
    print("[OK] Results saved to results/analytical_replicated_state.csv and results/cdc_ledger_history.csv")

def main():
    try:
        conn = get_connection()
        setup_schema(conn)
        generate_mutations(conn)
        test_interruption_recovery(conn)
        test_out_of_order_deduplication(conn)
        verify_consistency(conn)
        conn.close()
        print("\n==================================================")
        print("[SUCCESS] Practical 7 CDC Pipeline Verified!")
        print("==================================================")
    except Exception as e:
        print(f"\n[ERROR] PostgreSQL connection/execution failed: {e}")
        print("Please ensure PostgreSQL is running with credentials postgres/postgres.")
        sys.exit(1)

if __name__ == "__main__":
    main()
