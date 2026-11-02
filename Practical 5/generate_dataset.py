"""
generate_dataset.py
Practical 5: Multi-year partitioned analytical dataset generator.
Generates Hive-style partitions (year=YYYY/month=MM/region=REGION) for MinIO distributed storage.
"""

import os
import time
import numpy as np
import pandas as pd

def generate_partitioned_data(base_dir="data/partitions"):
    os.makedirs(base_dir, exist_ok=True)
    print("Generating multi-year partitioned analytical dataset...")
    
    np.random.seed(42)
    years = [2024, 2025]
    months = ["01", "02", "03"]
    regions = ["north", "south", "east", "west"]
    
    total_records = 0
    partition_paths = []
    
    for yr in years:
        for mo in months:
            for reg in regions:
                # Introduce realistic partition skew: 'west' has more volume, 'east' has less
                if reg == "west":
                    n_rows = 5000
                elif reg == "east":
                    n_rows = 1500
                else:
                    n_rows = 3000
                    
                total_records += n_rows
                
                # Partition directory structure
                part_dir = os.path.join(base_dir, f"year={yr}", f"month={mo}", f"region={reg}")
                os.makedirs(part_dir, exist_ok=True)
                file_path = os.path.join(part_dir, "data.csv")
                
                # Generate sample records
                df = pd.DataFrame({
                    "transaction_id": [f"TXN_{yr}{mo}_{reg[:2].upper()}_{i:05d}" for i in range(1, n_rows + 1)],
                    "timestamp": pd.date_range(start=f"{yr}-{mo}-01", periods=n_rows, freq="min").strftime("%Y-%m-%d %H:%M:%S"),
                    "customer_id": np.random.randint(1000, 9999, size=n_rows),
                    "year": yr,
                    "month": mo,
                    "region": reg,
                    "product_category": np.random.choice(["Electronics", "Home", "Apparel", "Beauty"], size=n_rows),
                    "amount": np.random.uniform(10.0, 500.0, size=n_rows).round(2)
                })
                
                df.to_csv(file_path, index=False)
                partition_paths.append((f"year={yr}/month={mo}/region={reg}/data.csv", file_path, n_rows))
                
    print(f"[OK] Generated {total_records:,} records across {len(partition_paths)} Hive partitions in '{base_dir}'.")
    return partition_paths

if __name__ == "__main__":
    generate_partitioned_data()
