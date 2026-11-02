"""
fraud_detection.py
Practical 10 Supplementary Problem:
5-Minute Per-User Rolling Fraud-Volume Check using sliding window aggregations.
"""

import os
import pandas as pd

def run_fraud_check():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("\n--------------------------------------------------")
    print("SUPPLEMENTARY PROBLEM: 5-MINUTE ROLLING FRAUD-VOLUME CHECK")
    print("--------------------------------------------------")
    
    df_txns = pd.read_csv("data/user_transactions.csv")
    df_txns["timestamp"] = pd.to_datetime(df_txns["timestamp"])
    df_txns = df_txns.sort_values(["user_id", "timestamp"]).reset_index(drop=True)
    
    print(f"Ingested {len(df_txns)} user transactions across {df_txns['user_id'].nunique()} users.")
    
    # Rolling 5-minute window per user
    alerts = []
    
    # Process each user's stream
    for user_id, group in df_txns.groupby("user_id"):
        group = group.sort_values("timestamp")
        
        for idx, current_txn in group.iterrows():
            curr_time = current_txn["timestamp"]
            window_start = curr_time - pd.Timedelta(minutes=5)
            
            # Find all transactions for this user within [curr_time - 5min, curr_time]
            window_txns = group[(group["timestamp"] >= window_start) & (group["timestamp"] <= curr_time)]
            
            window_count = len(window_txns)
            window_volume = round(window_txns["amount"].sum(), 2)
            
            # Fraud criteria: >= 3 transactions AND >= $1,000 within any 5-minute rolling window
            is_fraud = (window_count >= 3) and (window_volume >= 1000.0)
            
            if is_fraud:
                alerts.append({
                    "alert_time": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "user_id": user_id,
                    "trigger_txn_id": current_txn["txn_id"],
                    "window_start": window_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "window_end": curr_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "rolling_5min_txn_count": window_count,
                    "rolling_5min_volume": window_volume,
                    "risk_level": "CRITICAL - HIGH VELOCITY VOLUME SPIKE"
                })
                
    df_alerts = pd.DataFrame(alerts)
    if not df_alerts.empty:
        # Drop duplicates if multiple consecutive txns in same burst trigger alert
        df_alerts = df_alerts.drop_duplicates(subset=["user_id", "rolling_5min_txn_count"]).reset_index(drop=True)
        df_alerts.to_csv("results/fraud_alerts.csv", index=False)
        print(f"\n[ALERT] Detected {len(df_alerts)} Suspicious Fraud Activity Alerts:")
        print(df_alerts.to_string(index=False))
        print(f"\n[OK] Fraud alerts saved to results/fraud_alerts.csv")
    else:
        print("[OK] No fraud patterns detected within specified thresholds.")
        
    return df_alerts

if __name__ == "__main__":
    run_fraud_check()
