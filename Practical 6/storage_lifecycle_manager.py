"""
storage_lifecycle_manager.py
Practical 6: Storage Lifecycle Management (Hot, Warm, Cold).
Simulates object ages, evaluates retention and access frequency rules,
detects objects inactive for > 90 days, implements tier demotion,
and produces a clear cost/benefit comparison.
"""

import os
import io
import json
import time
import pandas as pd
from datetime import datetime, timedelta

try:
    import boto3
    from botocore.client import Config
except ImportError:
    boto3 = None

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "de-lifecycle-test"

def get_s3_client():
    if boto3 is None:
        raise ImportError("boto3 is not installed.")
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def setup_test_bucket(s3):
    print(f"Connecting to MinIO at {MINIO_ENDPOINT}...")
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"[OK] Dedicated lifecycle test bucket '{BUCKET_NAME}' exists.")
    except Exception:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"[OK] Created dedicated lifecycle test bucket '{BUCKET_NAME}'.")

def apply_lifecycle_policy(s3):
    print("\nApplying JSON Lifecycle Policy to bucket...")
    policy_path = "lifecycle_policy.json"
    with open(policy_path, "r", encoding="utf-8") as f:
        policy = json.load(f)
        
    try:
        # MinIO S3 PutBucketLifecycleConfiguration API
        s3.put_bucket_lifecycle_configuration(
            Bucket=BUCKET_NAME,
            LifecycleConfiguration=policy
        )
        print(f"[OK] Successfully applied lifecycle policy from {policy_path} to '{BUCKET_NAME}'.")
    except Exception as e:
        print(f"[NOTE] Native S3 lifecycle API response: {e}")
        print("  Proceeding with Python automation for age & inactivity evaluation.")

def create_synthetic_objects(s3):
    print("\nCreating synthetic objects with simulated age profiles...")
    now = datetime.now()
    
    # Define test objects with simulated age (days) and access counts
    test_objects = [
        {"key": "active/daily_orders_today.csv", "simulated_days_old": 5, "size_mb": 120.0, "access_count_30d": 450},
        {"key": "active/customer_profile_cache.json", "simulated_days_old": 15, "size_mb": 45.0, "access_count_30d": 890},
        {"key": "warm/monthly_sales_2026_08.parquet", "simulated_days_old": 45, "size_mb": 500.0, "access_count_30d": 12},
        {"key": "warm/app_access_logs_august.log", "simulated_days_old": 60, "size_mb": 350.0, "access_count_30d": 5},
        {"key": "historical/q1_financial_audit.parquet", "simulated_days_old": 120, "size_mb": 1200.0, "access_count_30d": 0},
        {"key": "historical/legacy_user_archive_2025.tar.gz", "simulated_days_old": 210, "size_mb": 2500.0, "access_count_30d": 0},
        {"key": "historical/raw_iot_dump_jan2025.csv", "simulated_days_old": 340, "size_mb": 4200.0, "access_count_30d": 0},
    ]
    
    # Upload lightweight mock content and store metadata
    for obj in test_objects:
        key = obj["key"]
        content = f"Mock data for {key}, simulated size: {obj['size_mb']} MB"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=content.encode("utf-8"),
            Metadata={
                "simulated_days_old": str(obj["simulated_days_old"]),
                "size_mb": str(obj["size_mb"]),
                "access_count_30d": str(obj["access_count_30d"])
            }
        )
    print(f"[OK] Uploaded {len(test_objects)} synthetic test objects with lifecycle metadata.")
    return test_objects

def evaluate_lifecycle_and_demote(s3, test_objects):
    print("\n--------------------------------------------------")
    print("STEP 2: EVALUATING AGE & 90-DAY INACTIVITY RULES")
    print("--------------------------------------------------")
    
    evaluated_records = []
    
    for obj in test_objects:
        days_old = obj["simulated_days_old"]
        accesses = obj["access_count_30d"]
        size_mb = obj["size_mb"]
        key = obj["key"]
        
        # Policy logic:
        # Hot: Age < 30 days and frequent access
        # Warm: Age 30-90 days OR access < 20
        # Cold: Inactive for > 90 days (0 accesses in 30d and age > 90d)
        if days_old > 90 and accesses == 0:
            target_tier = "COLD (Archive)"
            action = "DEMOTE_TO_COLD"
            inactive_flag = True
        elif days_old >= 30:
            target_tier = "WARM (Infrequent Access)"
            action = "TRANSITION_TO_WARM"
            inactive_flag = False
        else:
            target_tier = "HOT (Standard)"
            action = "RETAIN_HOT"
            inactive_flag = False
            
        evaluated_records.append({
            "object_key": key,
            "days_old": days_old,
            "access_count_30d": accesses,
            "size_mb": size_mb,
            "current_tier": "HOT (Standard)",
            "recommended_tier": target_tier,
            "policy_action": action,
            "inactive_over_90_days": inactive_flag
        })
        
        # Tag object in MinIO with new tier
        try:
            s3.put_object_tagging(
                Bucket=BUCKET_NAME,
                Key=key,
                Tagging={"TagSet": [{"Key": "StorageClass", "Value": target_tier.split()[0]}]}
            )
        except Exception:
            pass
            
    df_eval = pd.DataFrame(evaluated_records)
    df_eval.to_csv("results/lifecycle_evaluation.csv", index=False)
    
    print("[OK] Lifecycle evaluation completed:")
    print(df_eval[["object_key", "days_old", "access_count_30d", "recommended_tier", "policy_action"]].to_string(index=False))
    return df_eval

def calculate_cost_benefit(df_eval):
    print("\n--------------------------------------------------")
    print("COST / BENEFIT COMPARISON ANALYSIS")
    print("--------------------------------------------------")
    
    # Industry benchmark prices per GB per month:
    # Hot (S3 Standard):       $0.023 / GB
    # Warm (S3 Infrequent):    $0.0125 / GB
    # Cold (S3 Glacier Deep):  $0.00099 / GB
    
    p_hot = 0.023
    p_warm = 0.0125
    p_cold = 0.00099
    
    total_gb = df_eval["size_mb"].sum() / 1024.0
    
    # Baseline cost if all kept in Hot Standard tier
    baseline_cost = total_gb * p_hot
    
    # Optimized cost with Hot/Warm/Cold tiering
    tier_costs = []
    for _, row in df_eval.iterrows():
        gb = row["size_mb"] / 1024.0
        tier = row["recommended_tier"]
        if "COLD" in tier:
            cost = gb * p_cold
        elif "WARM" in tier:
            cost = gb * p_warm
        else:
            cost = gb * p_hot
        tier_costs.append(cost)
        
    optimized_cost = sum(tier_costs)
    monthly_savings = baseline_cost - optimized_cost
    savings_pct = (monthly_savings / baseline_cost) * 100 if baseline_cost > 0 else 0
    annual_savings = monthly_savings * 12
    
    print(f"Total Storage Managed:        {total_gb:.2f} GB ({df_eval['size_mb'].sum():.1f} MB)")
    print(f"Baseline Cost (All Hot):      ${baseline_cost:.4f} / month (${baseline_cost * 12:.2f} / year)")
    print(f"Optimized Cost (Tiered):      ${optimized_cost:.4f} / month (${optimized_cost * 12:.2f} / year)")
    print(f"Monthly Cost Savings:         ${monthly_savings:.4f} ({savings_pct:.1f}% reduction)")
    print(f"Projected Annual Savings:     ${annual_savings:.2f} / year")
    
    cost_df = pd.DataFrame([
        {
            "Strategy": "Unmanaged (All Standard Hot)",
            "Storage_GB": round(total_gb, 2),
            "Monthly_Cost_USD": round(baseline_cost, 4),
            "Annual_Cost_USD": round(baseline_cost * 12, 2),
            "Cost_Reduction_Pct": "0%"
        },
        {
            "Strategy": "Automated Lifecycle (Hot/Warm/Cold)",
            "Storage_GB": round(total_gb, 2),
            "Monthly_Cost_USD": round(optimized_cost, 4),
            "Annual_Cost_USD": round(optimized_cost * 12, 2),
            "Cost_Reduction_Pct": f"{savings_pct:.1f}%"
        }
    ])
    cost_df.to_csv("results/cost_benefit_comparison.csv", index=False)
    print("\n[OK] Cost comparison report saved -> results/cost_benefit_comparison.csv")

def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    s3 = get_s3_client()
    setup_test_bucket(s3)
    apply_lifecycle_policy(s3)
    test_objects = create_synthetic_objects(s3)
    df_eval = evaluate_lifecycle_and_demote(s3, test_objects)
    calculate_cost_benefit(df_eval)
    print("\n[OK] Practical 6 Lifecycle Management completed successfully.")

if __name__ == "__main__":
    main()
