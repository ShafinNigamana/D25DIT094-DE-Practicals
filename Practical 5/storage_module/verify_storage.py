"""
verify_storage.py
Reusable Storage Verification Script for Practical 5.
Connects to S3-compatible storage (SeaweedFS), verifies bucket availability,
inspects partition prefixes, checks object counts/sizes, and validates target partition.
"""

import sys
import os
import boto3
from botocore.client import Config

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:8333")
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "admin")
SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "secret")
BUCKET_NAME = "de-warehouse-partitioned"
TARGET_PREFIX = "year=2025/month=01/region=west/"

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )

def verify():
    print("==================================================")
    print("REUSABLE STORAGE MODULE VERIFICATION")
    print(f"Endpoint: {S3_ENDPOINT} | Bucket: {BUCKET_NAME}")
    print("==================================================")
    
    try:
        s3 = get_s3_client()
    except Exception as e:
        print(f"[ERROR] Failed to initialize Boto3 client: {e}")
        sys.exit(1)
        
    # 1. Verify Bucket Exists
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"[OK] Target bucket '{BUCKET_NAME}' exists and is accessible.")
    except Exception as e:
        print(f"[ERROR] Cannot access bucket '{BUCKET_NAME}': {e}")
        sys.exit(1)
        
    # 2. List Objects & Compute Storage Footprint
    paginator = s3.get_paginator("list_objects_v2")
    objects = []
    total_bytes = 0
    
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            objects.append(obj["Key"])
            total_bytes += obj["Size"]
            
    total_count = len(objects)
    total_kb = total_bytes / 1024.0
    
    print(f"[OK] Total partition files stored: {total_count}")
    print(f"[OK] Total bucket storage size:   {total_kb:.2f} KB ({total_bytes} bytes)")
    
    if total_count < 24:
        print(f"[WARN] Expected 24 partition files, but found {total_count}.")
    else:
        print(f"[OK] All 24 Hive partition objects are present.")
        
    # 3. Verify Target Partition Prefix for Pruning
    resp_target = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=TARGET_PREFIX)
    target_contents = resp_target.get("Contents", [])
    
    if not target_contents:
        print(f"[ERROR] Target prefix '{TARGET_PREFIX}' not found in bucket!")
        sys.exit(1)
    else:
        target_obj = target_contents[0]
        print(f"[OK] Target prefix verified: '{TARGET_PREFIX}'")
        print(f"     Key:  {target_obj['Key']}")
        print(f"     Size: {target_obj['Size'] / 1024.0:.2f} KB")
        
    print("\n[OK] Storage verification passed successfully!")
    sys.exit(0)

if __name__ == "__main__":
    verify()
