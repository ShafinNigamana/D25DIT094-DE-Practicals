import pandas as pd

df=pd.read_csv("data/customer.csv")

bad=df[df["Email"].isnull()]

bad.to_csv("quarantine/bad_records.csv",index=False)

print("Bad Records Saved")

# import pandas as pd

# df=pd.read_csv("data/customer.csv")

# print(df.isnull().sum())