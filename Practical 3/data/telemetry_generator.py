"""Generate realistic synthetic web and server telemetry events."""

import argparse
import json
import random
import time
from typing import Iterator


EVENT_TYPES = ("page_view", "search", "login", "purchase", "api_call")
SERVER_IDS = ("server-01", "server-02", "server-03", "server-04")


def create_event(event_id: int) -> dict:
    """Create one telemetry event with an event-time timestamp."""
    return {
        "event_id": event_id,
        "user_id": random.randint(100, 9999),
        "event_type": random.choice(EVENT_TYPES),
        "server_id": random.choice(SERVER_IDS),
        "cpu_percent": round(random.uniform(15.0, 95.0), 2),
        "memory_percent": round(random.uniform(25.0, 92.0), 2),
        "response_time_ms": round(random.uniform(20.0, 900.0), 2),
        "timestamp": time.time(),
    }


def event_stream(rate: float, duration: float, start_id: int = 1001) -> Iterator[dict]:
    """Yield events at approximately rate events/second for duration seconds."""
    if rate <= 0 or duration <= 0:
        return

    interval = 1.0 / rate
    end_time = time.monotonic() + duration
    event_id = start_id
    next_event_time = time.monotonic()

    while time.monotonic() < end_time:
        yield create_event(event_id)
        event_id += 1
        next_event_time += interval
        remaining = next_event_time - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)


def generate_events(rate: float, duration: float, start_id: int = 1001) -> list[dict]:
    """Return a finite list of generated events for file or batch use."""
    return list(event_stream(rate, duration, start_id))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sample telemetry JSON lines")
    parser.add_argument("--rate", type=float, default=10.0, help="Events per second")
    parser.add_argument("--duration", type=float, default=5.0, help="Duration in seconds")
    parser.add_argument("--output", help="Optional JSON-lines output file")
    args = parser.parse_args()

    output = open(args.output, "w", encoding="utf-8") if args.output else None
    try:
        count = 0
        for event in event_stream(args.rate, args.duration):
            line = json.dumps(event)
            if output:
                output.write(line + "\n")
            else:
                print(line)
            count += 1
        print(f"Generated {count} events at requested rate {args.rate:g}/sec")
    finally:
        if output:
            output.close()


if __name__ == "__main__":
    main()
