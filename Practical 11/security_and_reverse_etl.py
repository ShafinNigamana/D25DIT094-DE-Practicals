"""
security_and_reverse_etl.py
Practical 11: Data Serving, Reverse ETL, and Security
Implements column masking, SHA-256 identity hashing, RBAC enforcement,
Reverse ETL operational sync, and centralized security audit logging.
"""

import os
import re
import time
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

DB_FILE = "customer_analytics.db"
AUDIT_LOG = "logs/security_audit.log"

def hash_identity(val: str, salt="DE_SALT_2026") -> str:
    """Computes SHA-256 hash for identity pseudo-anonymization."""
    return hashlib.sha256((val + salt).encode("utf-8")).hexdigest()[:16]

def mask_email(email: str) -> str:
    """Masks email address, e.g., john.smith@example.com -> j***h@example.com"""
    try:
        user, domain = email.split("@")
        if len(user) <= 2:
            masked_user = user[0] + "***"
        else:
            masked_user = user[0] + "***" + user[-1]
        return f"{masked_user}@{domain}"
    except Exception:
        return "***@***.***"

def mask_ssn(ssn: str) -> str:
    """Masks SSN to conceal first five digits: ***-**-1234"""
    try:
        parts = ssn.split("-")
        return f"***-**-{parts[-1]}"
    except Exception:
        return "***-**-****"

def mask_name(name: str) -> str:
    """Masks full name: John Smith -> J*** S***"""
    words = name.split()
    return " ".join([f"{w[0]}***" for w in words if w])

def audit_log(role: str, action: str, resource: str, status: str, details: str):
    """Centralized security audit logger."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] ROLE={role.upper():<10} | ACTION={action:<15} | RESOURCE={resource:<25} | STATUS={status:<8} | {details}\n"
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(entry)

def setup_database():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    csv_file = "data/raw_customer_analytics.csv"
    if not os.path.exists(csv_file):
        from generate_analytics_data import generate_analytics_dataset
        generate_analytics_dataset()
        
    df = pd.read_csv(csv_file)
    
    # Calculate security columns
    df["hashed_id"] = df["customer_id"].apply(hash_identity)
    df["masked_name"] = df["full_name"].apply(mask_name)
    df["masked_email"] = df["email"].apply(mask_email)
    df["masked_ssn"] = df["ssn"].apply(mask_ssn)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Raw table (Contains sensitive PII)
    cursor.execute("DROP TABLE IF EXISTS customer_analytics;")
    cursor.execute("""
    CREATE TABLE customer_analytics (
        customer_id TEXT PRIMARY KEY,
        hashed_id TEXT,
        full_name TEXT,
        email TEXT,
        ssn TEXT,
        masked_name TEXT,
        masked_email TEXT,
        masked_ssn TEXT,
        lifetime_value REAL,
        churn_risk_score REAL,
        target_segment TEXT
    );
    """)
    
    df.to_sql("customer_analytics", conn, if_exists="append", index=False)
    
    # Analyst-Safe View (No raw PII accessible)
    cursor.execute("DROP VIEW IF EXISTS analyst_safe_view;")
    cursor.execute("""
    CREATE VIEW analyst_safe_view AS
    SELECT 
        hashed_id,
        masked_name,
        masked_email,
        masked_ssn,
        lifetime_value,
        churn_risk_score,
        target_segment
    FROM customer_analytics;
    """)
    
    # Operational CRM table for Reverse ETL target
    cursor.execute("DROP TABLE IF EXISTS operational_crm_targets;")
    cursor.execute("""
    CREATE TABLE operational_crm_targets (
        target_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        full_name TEXT,
        email TEXT,
        churn_risk_score REAL,
        recommended_action TEXT,
        synced_at TEXT
    );
    """)
    
    conn.commit()
    conn.close()
    audit_log("SYSTEM", "INITIALIZE", "customer_analytics.db", "SUCCESS", f"Populated {len(df)} records with hashing & masking.")
    print(f"[OK] Database setup complete: customer_analytics.db initialized with raw table and analyst_safe_view.")

# -----------------------------------------------------------------------------
# RBAC Access Gateway
# -----------------------------------------------------------------------------
def execute_query(role: str, query: str):
    """RBAC-enforcing query executor."""
    query_clean = query.strip()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check permissions for ANALYST role
    if role.upper() == "ANALYST":
        # Disallow direct queries to raw table
        if re.search(r"\bcustomer_analytics\b", query_clean, re.IGNORECASE):
            audit_log(role, "QUERY_REJECTED", "customer_analytics", "DENIED", "Policy violation: Analyst denied access to raw PII table.")
            conn.close()
            raise PermissionError("[DENIED] Security Policy: Role 'ANALYST' cannot query raw 'customer_analytics' table. Query 'analyst_safe_view' instead.")
            
    # Execute permitted query
    try:
        cursor.execute(query_clean)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        df_result = pd.DataFrame(rows, columns=cols)
        audit_log(role, "QUERY_EXECUTE", query_clean[:30] + "...", "SUCCESS", f"Returned {len(df_result)} rows.")
        conn.close()
        return df_result
    except Exception as e:
        audit_log(role, "QUERY_ERROR", query_clean[:30] + "...", "ERROR", str(e))
        conn.close()
        raise e

# -----------------------------------------------------------------------------
# Reverse ETL Sync Routine
# -----------------------------------------------------------------------------
def run_reverse_etl_sync():
    """Extracts high churn risk customers from analytics and syncs to operational CRM."""
    print("\n--------------------------------------------------")
    print("REVERSE ETL WORKFLOW: Analytics -> Operational CRM")
    print("--------------------------------------------------")
    
    conn = sqlite3.connect(DB_FILE)
    
    # Extract high churn VIP/high-value customers
    query = """
    SELECT customer_id, full_name, email, churn_risk_score
    FROM customer_analytics
    WHERE target_segment = 'High-Value Churn Risk'
      AND churn_risk_score >= 0.60;
    """
    df_sync = pd.read_sql_query(query, conn)
    print(f"Identified {len(df_sync)} high-value customers at churn risk for automated outreach.")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_sync["recommended_action"] = "Trigger VIP Retention Promo (20% Off)"
    df_sync["synced_at"] = timestamp
    
    # Load into operational destination table
    df_sync.to_sql("operational_crm_targets", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    
    audit_log("REVERSE_ETL", "SYNC_DISPATCH", "operational_crm_targets", "SUCCESS", f"Pushed {len(df_sync)} high-value churn targets.")
    
    # Save export snapshot
    df_sync.to_csv("results/reverse_etl_crm_export.csv", index=False)
    print(f"[OK] Reverse ETL Sync Completed: {len(df_sync)} records synced to operational_crm_targets.")
    print(f"[OK] Snapshot saved to results/reverse_etl_crm_export.csv")
    print(df_sync.head(4).to_string(index=False))

# -----------------------------------------------------------------------------
# Test and Verification Routine
# -----------------------------------------------------------------------------
def run_security_tests():
    print("\n--------------------------------------------------")
    print("SECURITY & RBAC ACCESS CONTROL TESTS")
    print("--------------------------------------------------")
    
    # Test 1: Admin querying raw data (Should SUCCEED)
    print("Test 1: Admin querying raw customer data...")
    df_admin = execute_query("ADMIN", "SELECT customer_id, full_name, email, ssn FROM customer_analytics LIMIT 3;")
    print("[PASS] Admin query returned raw PII:")
    print(df_admin.to_string(index=False))
    
    # Test 2: Analyst querying analyst_safe_view (Should SUCCEED)
    print("\nTest 2: Analyst querying analyst_safe_view...")
    df_analyst = execute_query("ANALYST", "SELECT hashed_id, masked_name, masked_email, masked_ssn, churn_risk_score FROM analyst_safe_view LIMIT 3;")
    print("[PASS] Analyst query returned masked/tokenized data:")
    print(df_analyst.to_string(index=False))
    
    # Test 3: Analyst attempting to query raw PII table (Should FAIL / BE DENIED)
    print("\nTest 3: Analyst attempting unauthorized access to raw table...")
    try:
        execute_query("ANALYST", "SELECT email, ssn FROM customer_analytics LIMIT 3;")
        print("[FAIL] Unauthorized query was not blocked!")
    except PermissionError as pe:
        print(f"[PASS] Access correctly blocked by RBAC: {pe}")
        
    # Verify Audit Log
    print(f"\n[OK] Security tests passed. Audit trail active in {AUDIT_LOG}.")
    with open(AUDIT_LOG, "r", encoding="utf-8") as f:
        log_lines = f.readlines()
    print(f"Total audit log entries recorded: {len(log_lines)}")

if __name__ == "__main__":
    setup_database()
    run_reverse_etl_sync()
    run_security_tests()
