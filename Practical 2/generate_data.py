from faker import Faker
import pandas as pd
import random

fake = Faker()

records = []

for i in range(20):

    records.append({

        "CustomerID": i+1,

        "Name": fake.name(),

        "Email": fake.email(),

        "Age": random.randint(18,60)

    })

df = pd.DataFrame(records)

df.to_csv("data/customer.csv",index=False)

print(df.head())