import json
import time
import uuid
import argparse

from kuksa_client.grpc import VSSClient, Datapoint


# Configuration
HOST = "127.0.0.1"
PORT = 55555

SIGNAL_PATH = "Vehicle.Perception.FrameData"


def publish_message(
    client,
    session_id,
    sequence_number,
    timestamp,
    detections=None
):

    detections = detections if detections is not None else []

    message = {
        "schema_version": 1,
        "source_id": "fault_injector",
        "session_id": session_id,
        "sequence_number": sequence_number,
        "capture_timestamp_ms": timestamp,
        "detection_count": len(detections),
        "detections": detections
    }

    client.set_current_values({
        SIGNAL_PATH: Datapoint(json.dumps(message))
    })

    print(f"Published sequence: {sequence_number}")
    print(f"Timestamp: {timestamp}")


def main():

    parser = argparse.ArgumentParser(
        description="SDV Perception Fault Injector"
    )

    parser.add_argument(
        "--scenario",
        choices=[
            "delay",
            "missing",
            "duplicate",
            "out_of_order",
            "stale",
            "invalid"
        ],
        required=True
    )

    args = parser.parse_args()

    session_id = str(uuid.uuid4())

    current_time = int(time.time() * 1000)

    with VSSClient(HOST, PORT) as client:

        print("\nStarting Fault Injection")
        print("Scenario:", args.scenario)
        print("Session ID:", session_id)
        print("-" * 45)

        # 1. DELAY FAULT
        if args.scenario == "delay":

            capture_time = int(time.time() * 1000)

            print("Capturing message timestamp...")
            print("Waiting 2 seconds before publishing...")

            time.sleep(2)

            publish_message(
                client,
                session_id,
                1,
                capture_time
            )

        # 2. MISSING MESSAGE FAULT
        elif args.scenario == "missing":

            publish_message(
                client,
                session_id,
                1,
                current_time
            )

            time.sleep(0.5)

            publish_message(
                client,
                session_id,
                3,
                int(time.time() * 1000)
            )

        # 3. DUPLICATE MESSAGE FAULT
        elif args.scenario == "duplicate":

            publish_message(
                client,
                session_id,
                1,
                current_time
            )

            time.sleep(0.5)

            publish_message(
                client,
                session_id,
                1,
                int(time.time() * 1000)
            )

        # 4. OUT-OF-ORDER MESSAGE FAULT
        elif args.scenario == "out_of_order":

            publish_message(
                client,
                session_id,
                2,
                current_time
            )

            time.sleep(0.5)

            publish_message(
                client,
                session_id,
                1,
                int(time.time() * 1000)
            )

        # 5. STALE MESSAGE FAULT
        elif args.scenario == "stale":

            old_timestamp = current_time - 2000

            publish_message(
                client,
                session_id,
                1,
                old_timestamp
            )

        # 6. INVALID MESSAGE FAULT
        elif args.scenario == "invalid":

            invalid_detection = [
                {
                    "class": "person",
                    "confidence": 1.5,
                    "bbox": [100, 100, 200, 300]
                }
            ]

            publish_message(
                client,
                session_id,
                1,
                current_time,
                invalid_detection
            )

            print("Injected invalid confidence value: 1.5")

        print("-" * 45)
        print("Fault injection completed.")


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nFault injection interrupted.")

    except Exception as error:
        print("Fault injection error:", error)
