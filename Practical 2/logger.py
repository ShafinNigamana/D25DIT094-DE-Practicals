import logging
import os

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    filename="logs/execution.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    logging.info("Program Started")
    logging.warning("Missing Email Found")
    logging.error("Primary Key Missing")
    print("Log Generated")