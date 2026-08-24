"""Print and optionally apply the Kafka partition-scaling experiment commands."""

import argparse
import subprocess


def main() -> None:
    parser = argparse.ArgumentParser(description="Scale telemetry partitions for a consumer-group demo")
    parser.add_argument("--topic", default="telemetry")
    parser.add_argument("--partitions", type=int, default=4)
    parser.add_argument("--bootstrap", default="localhost:9092")
    parser.add_argument("--apply", action="store_true", help="Run kafka-topics command")
    parser.add_argument("--kafka-home", help="Kafka installation directory")
    args = parser.parse_args()

    command = [
        "cmd.exe",
        "/c",
        "bin\\windows\\kafka-topics.bat",
        "--bootstrap-server",
        args.bootstrap,
        "--alter",
        "--topic",
        args.topic,
        "--partitions",
        str(args.partitions),
    ]
    print("Partition scaling command:")
    print(" ".join(command[3:]))
    print("Start up to one consumer per partition using the same --group value.")
    if args.apply:
        if not args.kafka_home:
            raise SystemExit("--kafka-home is required with --apply")
        subprocess.run(command, cwd=args.kafka_home, check=True)
        print(f"Topic {args.topic} now has at least {args.partitions} partitions")


if __name__ == "__main__":
    main()
