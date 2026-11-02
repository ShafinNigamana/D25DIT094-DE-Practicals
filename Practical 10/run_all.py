"""
run_all.py
Practical 10: Complete Batch and Streaming Pipeline Runner
Executes environment check, data generation, batch transformations,
streaming watermarking, and supplementary fraud detection.
"""

from check_environment import check_env
from generate_iot_data import generate_data
from batch_transformations import run_batch_pipeline
from streaming_watermark import run_streaming_watermark
from fraud_detection import run_fraud_check

def main():
    print("==================================================")
    print("STARTING PRACTICAL 10 PIPELINE EXECUTION")
    print("==================================================")
    
    # 1. Environment Check
    check_env()
    
    # 2. Data Generation
    generate_data()
    
    # 3. Batch Transformations
    run_batch_pipeline()
    
    # 4. Streaming Transformations with Watermark
    run_streaming_watermark()
    
    # 5. Supplementary Fraud Volume Check
    run_fraud_check()
    
    print("\n==================================================")
    print("[SUCCESS] Practical 10 executed completely and verified!")
    print("==================================================")

if __name__ == "__main__":
    main()
