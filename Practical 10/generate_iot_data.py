"""
generate_iot_data.py
Practical 10: Generates IoT telemetry (with out-of-order and late events),
device registry metadata, and user financial transactions for fraud checking.
"""

import os
import pandas as pd
import numpy as np

def generate_data():
    os.makedirs("data", exist_ok=True)
    np.random.seed(42)
    
    # 1. Device Metadata
    devices = [
        {"device_id": f"DEV_{i:03d}", "model": f"Sensor-X{i%3 + 1}", "location": loc, "firmware": "v2.1.4"}
        for i, loc in enumerate(["Sector-A", "Sector-B", "Sector-C", "Sector-D", "Sector-E"], start=1)
    ]
    df_devices = pd.DataFrame(devices)
    df_devices.to_csv("data/iot_metadata.csv", index=False)
    print(f"[OK] Generated {len(df_devices)} device metadata records -> data/iot_metadata.csv")
    
    # 2. Out-of-Order IoT Telemetry Events
    base_time = pd.Timestamp("2026-10-05 10:00:00")
    events = []
    
    # Generate 50 regular events arriving in sequence
    for i in range(1, 51):
        event_time = base_time + pd.Timedelta(seconds=i * 2)
        arrival_time = event_time + pd.Timedelta(milliseconds=np.random.randint(50, 300))
        dev = devices[i % len(devices)]["device_id"]
        
        # Introduce deliberate quality flaws in a few rows
        temp = round(float(np.random.uniform(20.0, 35.0)), 2)
        if i == 5:
            temp = np.nan  # Corrupt: Missing temperature
        battery = int(np.random.randint(50, 100))
        if i == 12:
            battery = -15  # Corrupt: Negative battery
            
        events.append({
            "event_id": f"EVT_{i:04d}",
            "device_id": dev,
            "event_time": event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "arrival_time": arrival_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "temperature": temp,
            "vibration": round(float(np.random.uniform(0.1, 1.5)), 3),
            "battery_level": battery
        })
        
    # Inject an out-of-order event arriving slightly late (within 10s watermark)
    in_watermark_event = {
        "event_id": "EVT_0099_OOO",
        "device_id": "DEV_001",
        "event_time": (base_time + pd.Timedelta(seconds=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "arrival_time": (base_time + pd.Timedelta(seconds=52)).strftime("%Y-%m-%d %H:%M:%S.100"),
        "temperature": 27.5,
        "vibration": 0.82,
        "battery_level": 88
    }
    events.insert(30, in_watermark_event)
    
    # Inject a GENUINELY LATE event (event time is 10:00:10, but arrives at 10:01:30, 80s late, beyond watermark)
    genuinely_late_event = {
        "event_id": "EVT_9999_LATE",
        "device_id": "DEV_002",
        "event_time": (base_time + pd.Timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "arrival_time": (base_time + pd.Timedelta(seconds=90)).strftime("%Y-%m-%d %H:%M:%S.500"),
        "temperature": 24.1,
        "vibration": 0.45,
        "battery_level": 92
    }
    events.append(genuinely_late_event)
    
    df_telemetry = pd.DataFrame(events)
    df_telemetry.to_csv("data/iot_telemetry.csv", index=False)
    print(f"[OK] Generated {len(df_telemetry)} IoT telemetry records (including out-of-order & late) -> data/iot_telemetry.csv")
    
    # 3. User Transactions for Supplementary Fraud-Volume Check
    # Simulate a user with high transaction frequency within a 5-minute window
    txn_base = pd.Timestamp("2026-10-05 12:00:00")
    txns = [
        # Normal user 1 (spaced out)
        {"txn_id": "TXN_101", "user_id": "USER_A", "timestamp": (txn_base + pd.Timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 50.0},
        {"txn_id": "TXN_102", "user_id": "USER_A", "timestamp": (txn_base + pd.Timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 75.0},
        
        # Fraud User B: 5 transactions within 3 minutes totaling $1,650 (Exceeds threshold)
        {"txn_id": "TXN_201", "user_id": "USER_B", "timestamp": (txn_base + pd.Timedelta(minutes=2, seconds=10)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 400.0},
        {"txn_id": "TXN_202", "user_id": "USER_B", "timestamp": (txn_base + pd.Timedelta(minutes=2, seconds=45)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 350.0},
        {"txn_id": "TXN_203", "user_id": "USER_B", "timestamp": (txn_base + pd.Timedelta(minutes=3, seconds=15)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 300.0},
        {"txn_id": "TXN_204", "user_id": "USER_B", "timestamp": (txn_base + pd.Timedelta(minutes=4, seconds=0)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 600.0},
        
        # Normal user C
        {"txn_id": "TXN_301", "user_id": "USER_C", "timestamp": (txn_base + pd.Timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 120.0},
        {"txn_id": "TXN_302", "user_id": "USER_C", "timestamp": (txn_base + pd.Timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S"), "amount": 80.0},
    ]
    df_txns = pd.DataFrame(txns)
    df_txns.to_csv("data/user_transactions.csv", index=False)
    print(f"[OK] Generated {len(df_txns)} user transaction records -> data/user_transactions.csv")

if __name__ == "__main__":
    generate_data()
