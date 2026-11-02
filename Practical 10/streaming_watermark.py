"""
streaming_watermark.py
Practical 10: Streaming Event-Time Processing with Watermark
Simulates continuous event streaming, manages dynamic watermarks,
and demonstrates the handling and dropping of late-arriving records.
"""

import os
import pandas as pd
from datetime import timedelta

def run_streaming_watermark():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("\n--------------------------------------------------")
    print("STEP 2: STREAMING EVENT-TIME PROCESSING WITH WATERMARK")
    print("--------------------------------------------------")
    
    df_raw = pd.read_csv("data/iot_telemetry.csv")
    df_metadata = pd.read_csv("data/iot_metadata.csv")
    
    # Merge metadata for enrichment
    df_stream = pd.merge(df_raw, df_metadata, on="device_id", how="left")
    df_stream["event_time"] = pd.to_datetime(df_stream["event_time"])
    df_stream["arrival_time"] = pd.to_datetime(df_stream["arrival_time"])
    
    # Sort by arrival_time to simulate the physical stream ingestion order
    df_stream = df_stream.sort_values("arrival_time").reset_index(drop=True)
    
    # Watermark configuration: allowed lateness = 15 seconds
    allowed_lateness = timedelta(seconds=15)
    max_event_time = df_stream.iloc[0]["event_time"]
    watermark = max_event_time - allowed_lateness
    
    accepted_events = []
    dropped_late_events = []
    
    print(f"Streaming Configuration: Allowed Lateness = {allowed_lateness.total_seconds()}s")
    print(f"Total stream events arriving: {len(df_stream)}")
    
    with open("logs/watermark_execution.log", "w", encoding="utf-8") as log:
        log.write("STREAMING EVENT-TIME PROCESSING AUDIT LOG\n")
        log.write("=" * 60 + "\n")
        
        for idx, row in df_stream.iterrows():
            evt_id = row["event_id"]
            dev_id = row["device_id"]
            e_time = row["event_time"]
            arr_time = row["arrival_time"]
            
            # Update max event time observed so far
            if e_time > max_event_time:
                max_event_time = e_time
                watermark = max_event_time - allowed_lateness
                
            # Watermark condition check
            if e_time >= watermark:
                # Event is on-time or acceptable out-of-order within watermark
                status = "ACCEPTED"
                accepted_events.append(row.to_dict())
                msg = f"[{arr_time}] {evt_id} ({dev_id}) EventTime={e_time} | Watermark={watermark} -> ACCEPTED"
            else:
                # Genuinely late event: event_time is older than watermark
                lateness_secs = (watermark - e_time).total_seconds()
                status = "DROPPED_LATE"
                dropped_row = row.to_dict()
                dropped_row["lateness_seconds"] = lateness_secs
                dropped_row["watermark_at_arrival"] = watermark
                dropped_late_events.append(dropped_row)
                msg = f"[{arr_time}] {evt_id} ({dev_id}) EventTime={e_time} | Watermark={watermark} -> DROPPED (Late by {lateness_secs:.1f}s)"
                
            log.write(msg + "\n")
            if "DROPPED" in status or "OOO" in evt_id:
                print(f"  {msg}")
                
    df_accepted = pd.DataFrame(accepted_events)
    df_dropped = pd.DataFrame(dropped_late_events)
    
    df_accepted.to_csv("results/streaming_accepted_events.csv", index=False)
    df_dropped.to_csv("results/late_dropped_events.csv", index=False)
    
    print(f"\n[OK] Streaming Event Processing Completed:")
    print(f"  - Accepted Events (on-time & within watermark): {len(df_accepted)}")
    print(f"  - Dropped Late Events (outside watermark):      {len(df_dropped)}")
    print(f"[OK] Late-arriving events quarantined in results/late_dropped_events.csv")
    print(f"[OK] Watermark audit log written to logs/watermark_execution.log")
    
    return df_accepted, df_dropped

if __name__ == "__main__":
    run_streaming_watermark()
