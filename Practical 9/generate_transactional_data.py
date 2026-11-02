"""
generate_transactional_data.py
Synthesizes a realistic e-commerce transactional dataset for Practical 9 (Data Modeling for Analytics).
"""

import os
import time
import numpy as np
import pandas as pd

def generate_transactions(output_path="raw_transactions.csv", num_records=50000):
    print(f"Generating {num_records:,} transactional order records...")
    start_time = time.time()
    np.random.seed(42)
    
    # Dimension entities
    customers = [
        (f"CUST{i:04d}", f"Customer_{i}", np.random.choice(["Retail", "Corporate", "Small Business"]),
         np.random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]), "USA")
        for i in range(1, 501)
    ]
    
    products = [
        # (id, name, subcategory, category)
        ("PROD001", "iPhone 15", "Smartphones", "Electronics"),
        ("PROD002", "Galaxy S24", "Smartphones", "Electronics"),
        ("PROD003", "MacBook Pro", "Laptops", "Electronics"),
        ("PROD004", "Dell XPS 15", "Laptops", "Electronics"),
        ("PROD005", "Noise-Cancelling Headphones", "Audio", "Electronics"),
        ("PROD006", "Office Desk Chair", "Chairs", "Furniture"),
        ("PROD007", "Standing Desk", "Desks", "Furniture"),
        ("PROD008", "Bookshelf 5-Tier", "Storage", "Furniture"),
        ("PROD009", "Running Shoes", "Footwear", "Apparel"),
        ("PROD010", "Winter Fleece Jacket", "Outerwear", "Apparel"),
    ]
    
    stores = [
        ("STORE01", "Manhattan Flagship", "New York", "USA"),
        ("STORE02", "LA Metro Mall", "Los Angeles", "USA"),
        ("STORE03", "Chicago Loop Store", "Chicago", "USA"),
        ("STORE04", "Houston Galleria", "Houston", "USA"),
        ("STORE05", "Online Direct Web", "Virtual", "Global"),
    ]
    
    dates = pd.date_range(start="2025-01-01", end="2025-12-31", freq="D")
    
    # Generate transactions
    records = []
    for i in range(1, num_records + 1):
        cust = customers[np.random.randint(0, len(customers))]
        prod = products[np.random.randint(0, len(products))]
        store = stores[np.random.randint(0, len(stores))]
        order_date = np.random.choice(dates)
        
        qty = int(np.random.choice([1, 2, 3, 4, 5], p=[0.5, 0.25, 0.15, 0.07, 0.03]))
        unit_price = {
            "PROD001": 999.0, "PROD002": 899.0, "PROD003": 1999.0, "PROD004": 1599.0,
            "PROD005": 299.0, "PROD006": 249.0, "PROD007": 499.0, "PROD008": 149.0,
            "PROD009": 119.0, "PROD010": 89.0
        }[prod[0]]
        
        discount_pct = float(np.random.choice([0.0, 0.05, 0.10, 0.15, 0.20], p=[0.6, 0.15, 0.15, 0.07, 0.03]))
        discount_amount = round(qty * unit_price * discount_pct, 2)
        total_amount = round((qty * unit_price) - discount_amount, 2)
        
        records.append({
            "line_item_id": i,
            "order_id": f"ORD{np.random.randint(10000, 25000):05d}",
            "order_date": pd.Timestamp(order_date).strftime("%Y-%m-%d"),
            "customer_id": cust[0],
            "customer_name": cust[1],
            "customer_segment": cust[2],
            "customer_city": cust[3],
            "customer_country": cust[4],
            "product_id": prod[0],
            "product_name": prod[1],
            "product_subcategory": prod[2],
            "product_category": prod[3],
            "store_id": store[0],
            "store_name": store[1],
            "store_city": store[2],
            "store_country": store[3],
            "quantity": qty,
            "unit_price": unit_price,
            "discount_amount": discount_amount,
            "total_amount": total_amount
        })
        
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    elapsed = time.time() - start_time
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"[OK] Generated {num_records:,} transactional records in {elapsed:.2f}s -> {output_path} ({file_size_mb:.2f} MB)")
    return output_path

if __name__ == "__main__":
    generate_transactions()
