import sqlite3
import pandas as pd

conn=sqlite3.connect("customer.db")

df=pd.read_csv("data/customer.csv")

df.to_sql("Customer",conn,if_exists="replace",index=False)

print("Database Created")