import pandas as pd

df=pd.read_csv("data/customer.csv")

print(df.columns)

print(df.dtypes)

print(df.describe())