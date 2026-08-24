from pathlib import Path
import time


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "user_activity.log"


def main():
    print("\n--- Streaming-style Ingestion ---")
    print("Reading the log file and simulating continuous event arrival.")

    with LOG_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            event = line.strip()
            if not event:
                continue

            print(f"\nIncoming event: {event}")
            print("Processing event...")
            time.sleep(1)

    print("\nStreaming ingestion completed.")


if __name__ == "__main__":
    main()
