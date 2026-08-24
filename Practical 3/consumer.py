from kafka import KafkaConsumer
import json
import time


# NEW: Safely decode JSON messages.
# If the message is not JSON, return it as normal text instead of crashing.
def safe_json_loads(x):
    try:
        return json.loads(x.decode("utf-8"))
    except json.JSONDecodeError:
        return x.decode("utf-8")


consumer = KafkaConsumer(
    "student_latency",
    bootstrap_servers="localhost:9092",

    # Read old messages if this consumer has no saved offset.
    auto_offset_reset="earliest",

    # OLD: Crashes when a non-JSON message is encountered.
    # value_deserializer=lambda x: json.loads(x.decode("utf-8"))

    # NEW: Handles both JSON and plain-text messages safely.
    value_deserializer=lambda x: safe_json_loads(x)
)


print("Waiting for messages...")

count = 0
start_time = time.time()
total_latency = 0


for message in consumer:

    data = message.value

    # NEW: Our old manual test messages are plain text.
    # They don't contain a timestamp, so we cannot calculate latency for them.
    if not isinstance(data, dict):
        print("Skipped non-JSON message:", data)
        continue

    receive_time = time.time()

    latency = (receive_time - data["timestamp"]) * 1000

    total_latency += latency
    count += 1

    print("Received:", data)
    print("Latency:", latency, "ms")

    # Stop after processing 3 valid student messages.
    if count == 3:
        break


end_time = time.time()
total_time = end_time - start_time

if count > 0:
    avg_latency = total_latency / count
    throughput = count / total_time

    print("\nAverage Latency:", avg_latency, "ms")
    print("Throughput:", throughput, "messages/sec")
else:
    print("\nNo valid JSON messages were processed.")


consumer.close()
print("Consumer finished")