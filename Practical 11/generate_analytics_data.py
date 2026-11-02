"""
generate_analytics_data.py
Practical 11: Data Serving, Reverse ETL, and Security
Generates synthetic customer analytics dataset containing PII, lifetime value, and churn scores.
"""

import os
import pandas as pd
import numpy as np

def generate_analytics_dataset(output_path="raw_customer_analytics.csv", num_records=1000):
    os.makedirs("data", exist_ok=True)
    np.random.seed(42)
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    domains = ["example.com", "mailcorp.net", "techweb.org", "servicehub.io"]
    segments = ["High-Value Churn Risk", "Loyal VIP", "Promising Growth", "Standard", "At-Risk Low-Value"]
    
    records = []
    for i in range(1, num_records + 1):
        fn = np.random.choice(first_names)
        ln = np.random.choice(last_names)
        full_name = f"{fn} {ln}"
        email = f"{fn.lower()}.{ln.lower()}{i%50}@{np.random.choice(domains)}"
        ssn = f"{np.random.randint(100, 999)}-{np.random.randint(10, 99)}-{np.random.randint(1000, 9999)}"
        ltv = round(float(np.random.uniform(100.0, 5000.0)), 2)
        churn_score = round(float(np.random.beta(a=2, b=5)), 3) # Skewed towards low/mid
        
        # Segment assignment
        if ltv > 2500 and churn_score > 0.60:
            segment = "High-Value Churn Risk"
        elif ltv > 3000:
            segment = "Loyal VIP"
        elif churn_score > 0.65:
            segment = "At-Risk Low-Value"
        elif ltv > 1500:
            segment = "Promising Growth"
        else:
            segment = "Standard"
            
        records.append({
            "customer_id": f"CUST_{i:05d}",
            "full_name": full_name,
            "email": email,
            "ssn": ssn,
            "lifetime_value": ltv,
            "churn_risk_score": churn_score,
            "target_segment": segment
        })
        
    df = pd.DataFrame(records)
    target_file = os.path.join("data", output_path)
    df.to_csv(target_file, index=False)
    print(f"[OK] Generated {num_records:,} customer analytics records -> {target_file}")
    return target_file

if __name__ == "__main__":
    generate_analytics_dataset()
