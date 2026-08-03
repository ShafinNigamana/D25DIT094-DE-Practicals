import json

transactions=[]

for i in range(10):

    transactions.append({

        "TransactionID":100+i,

        "Customer":{

            "ID":i,

            "Name":"Customer"+str(i)

        },

        "Payment":{

            "Amount":500,

            "Mode":"UPI"

        }

    })

with open("data/api.json","w") as f:

    json.dump(transactions,f,indent=4)

print("JSON Created")