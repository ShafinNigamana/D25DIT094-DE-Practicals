"""
query_optimization.py
Practical 8: Query Processing and Optimization
Benchmarks baseline vs optimized analytical queries in DuckDB,
captures EXPLAIN / EXPLAIN ANALYZE execution plans, and implements
the supplementary CTE / Window Function nested query rewrite.
"""

import os
import time
import duckdb
import pandas as pd

def run_query_optimization():
    csv_file = "clickstream.csv"
    if not os.path.exists(csv_file):
        from generate_clickstream import generate_clickstream
        generate_clickstream(csv_file, num_records=500000)
        
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("\n==================================================")
    print("PRACTICAL 8: QUERY PROCESSING AND OPTIMIZATION")
    print("==================================================")
    
    # Connect to in-memory DuckDB for fast OLAP analytics
    con = duckdb.connect(database=":memory:")
    
    # Load dataset
    print(f"\n1. Loading {csv_file} into DuckDB...")
    t0 = time.time()
    con.execute(f"CREATE TABLE clickstream AS SELECT * FROM read_csv_auto('{csv_file}')")
    load_time = time.time() - t0
    
    row_count = con.execute("SELECT COUNT(*) FROM clickstream").fetchone()[0]
    print(f"[OK] Loaded {row_count:,} rows into DuckDB table 'clickstream' in {load_time:.2f}s")
    
    # -------------------------------------------------------------------------
    # WORKLOAD 1: Analytical Query Optimization
    # -------------------------------------------------------------------------
    print("\n--------------------------------------------------")
    print("WORKLOAD 1: User Purchase & Funnel Analytics")
    print("--------------------------------------------------")
    
    # Baseline Query: Multiple correlated subqueries and unoptimized multi-pass scans
    baseline_sql = """
    SELECT 
        user_id,
        (SELECT COUNT(*) FROM clickstream c2 WHERE c2.user_id = c1.user_id) AS total_events,
        SUM(purchase_amount) AS total_spent,
        AVG(duration_sec) AS avg_duration
    FROM clickstream c1
    WHERE event_type = 'purchase'
      AND purchase_amount > (SELECT AVG(purchase_amount) FROM clickstream WHERE event_type = 'purchase')
    GROUP BY user_id
    HAVING SUM(purchase_amount) > 500
    ORDER BY total_spent DESC
    LIMIT 20;
    """
    
    # Optimized Query: Single pass aggregation with CTE, pushing down filter early
    optimized_sql = """
    WITH purchase_threshold AS (
        SELECT AVG(purchase_amount) AS avg_purchase
        FROM clickstream
        WHERE event_type = 'purchase'
    ),
    user_event_counts AS (
        SELECT user_id, COUNT(*) AS total_events
        FROM clickstream
        GROUP BY user_id
    ),
    qualified_purchases AS (
        SELECT 
            c.user_id,
            SUM(c.purchase_amount) AS total_spent,
            AVG(c.duration_sec) AS avg_duration
        FROM clickstream c
        CROSS JOIN purchase_threshold pt
        WHERE c.event_type = 'purchase'
          AND c.purchase_amount > pt.avg_purchase
        GROUP BY c.user_id
        HAVING SUM(c.purchase_amount) > 500
    )
    SELECT 
        qp.user_id,
        uec.total_events,
        qp.total_spent,
        qp.avg_duration
    FROM qualified_purchases qp
    JOIN user_event_counts uec ON qp.user_id = uec.user_id
    ORDER BY qp.total_spent DESC
    LIMIT 20;
    """
    
    # Capture Execution Plans
    print("\nCapturing EXPLAIN plans for Workload 1...")
    baseline_plan = con.execute(f"EXPLAIN {baseline_sql}").fetchall()[0][1]
    optimized_plan = con.execute(f"EXPLAIN {optimized_sql}").fetchall()[0][1]
    
    with open("results/workload1_baseline_plan.txt", "w", encoding="utf-8") as f:
        f.write(baseline_plan)
    with open("results/workload1_optimized_plan.txt", "w", encoding="utf-8") as f:
        f.write(optimized_plan)
        
    # Execute Baseline
    t_start = time.time()
    df_baseline = con.execute(baseline_sql).fetchdf()
    t_base = time.time() - t_start
    print(f"  -> Baseline Runtime:  {t_base*1000:.2f} ms ({t_base:.4f} s)")
    
    # Execute Optimized
    t_start = time.time()
    df_optimized = con.execute(optimized_sql).fetchdf()
    t_opt = time.time() - t_start
    print(f"  -> Optimized Runtime: {t_opt*1000:.2f} ms ({t_opt:.4f} s)")
    
    speedup = t_base / t_opt if t_opt > 0 else 1.0
    print(f"  -> Speedup Factor:    {speedup:.2f}x faster")
    
    # Verify logical equivalence
    # Compare rounded values to avoid tiny floating point differences
    pd.testing.assert_frame_equal(df_baseline.round(2), df_optimized.round(2))
    print("  [OK] Logical verification passed: Baseline and Optimized results are IDENTICAL.")
    
    # -------------------------------------------------------------------------
    # SUPPLEMENTARY PROBLEM: Nested Correlated Query Rewrite using Window Functions
    # -------------------------------------------------------------------------
    print("\n--------------------------------------------------")
    print("SUPPLEMENTARY PROBLEM: Nested Query Rewrite using Window Functions")
    print("--------------------------------------------------")
    print("Goal: Retrieve top 3 sessions with longest duration for each device type.")
    
    # Use a realistic subset of distinct sessions for benchmark comparison
    con.execute("""
    CREATE TEMP TABLE device_sessions AS 
    SELECT device, session_id, MAX(duration_sec) AS max_duration
    FROM clickstream
    GROUP BY device, session_id
    LIMIT 5000;
    """)
    
    # Baseline Nested Query (Correlated Subquery)
    supp_baseline_sql = """
    SELECT s1.device, s1.session_id, s1.max_duration
    FROM device_sessions s1
    WHERE (
        SELECT COUNT(DISTINCT s2.max_duration)
        FROM device_sessions s2
        WHERE s2.device = s1.device AND s2.max_duration >= s1.max_duration
    ) <= 3
    ORDER BY s1.device, s1.max_duration DESC;
    """
    
    # Optimized Query with CTE and Window Function (DENSE_RANK)
    supp_optimized_sql = """
    WITH ranked_sessions AS (
        SELECT 
            device, 
            session_id, 
            max_duration,
            DENSE_RANK() OVER (PARTITION BY device ORDER BY max_duration DESC) AS rank_pos
        FROM device_sessions
    )
    SELECT device, session_id, max_duration
    FROM ranked_sessions
    WHERE rank_pos <= 3
    ORDER BY device, max_duration DESC;
    """
    
    supp_base_plan = con.execute(f"EXPLAIN {supp_baseline_sql}").fetchall()[0][1]
    supp_opt_plan = con.execute(f"EXPLAIN {supp_optimized_sql}").fetchall()[0][1]
    
    with open("results/supplementary_baseline_plan.txt", "w", encoding="utf-8") as f:
        f.write(supp_base_plan)
    with open("results/supplementary_optimized_plan.txt", "w", encoding="utf-8") as f:
        f.write(supp_opt_plan)
        
    t_start = time.time()
    df_supp_base = con.execute(supp_baseline_sql).fetchdf()
    t_supp_base = time.time() - t_start
    print(f"  -> Correlated Subquery Runtime:  {t_supp_base*1000:.2f} ms ({t_supp_base:.4f} s)")
    
    t_start = time.time()
    df_supp_opt = con.execute(supp_optimized_sql).fetchdf()
    t_supp_opt = time.time() - t_start
    print(f"  -> Window Function CTE Runtime:  {t_supp_opt*1000:.2f} ms ({t_supp_opt:.4f} s)")
    
    supp_speedup = t_supp_base / t_supp_opt if t_supp_opt > 0 else 1.0
    print(f"  -> Supplementary Speedup:        {supp_speedup:.2f}x faster")
    
    # Verify equivalence
    pd.testing.assert_frame_equal(df_supp_base, df_supp_opt)
    print("  [OK] Supplementary verification passed: Window Function matches Nested Query exactly!")
    
    # -------------------------------------------------------------------------
    # Save Benchmark Report
    # -------------------------------------------------------------------------
    benchmark_df = pd.DataFrame([
        {
            "Workload": "Workload 1 (Purchase Analytics)",
            "Query Type": "Baseline (Correlated Subquery)",
            "Runtime_ms": round(t_base * 1000, 2),
            "Bottleneck": "Correlated subquery per-row scan & redundant passes"
        },
        {
            "Workload": "Workload 1 (Purchase Analytics)",
            "Query Type": "Optimized (CTE + Filter Pushdown)",
            "Runtime_ms": round(t_opt * 1000, 2),
            "Bottleneck": "Eliminated subqueries; single pass Hash Join"
        },
        {
            "Workload": "Supplementary (Top Sessions by Device)",
            "Query Type": "Baseline (Nested Correlated Subquery)",
            "Runtime_ms": round(t_supp_base * 1000, 2),
            "Bottleneck": "O(N^2) quadratic correlated nested count"
        },
        {
            "Workload": "Supplementary (Top Sessions by Device)",
            "Query Type": "Optimized (DENSE_RANK Window Function CTE)",
            "Runtime_ms": round(t_supp_opt * 1000, 2),
            "Bottleneck": "Linear O(N log N) partitioned window sort"
        }
    ])
    
    benchmark_df.to_csv("results/optimization_benchmarks.csv", index=False)
    print("\nBenchmark results saved to results/optimization_benchmarks.csv")
    print(benchmark_df.to_string(index=False))
    
    print("\n[OK] Practical 8 execution completed successfully.")
    con.close()

if __name__ == "__main__":
    run_query_optimization()
