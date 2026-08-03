import logging

logging.basicConfig(

filename="logs/execution.log",

level=logging.INFO

)

logging.info("Program Started")

logging.warning("Missing Email Found")

logging.error("Primary Key Missing")

print("Log Generated")