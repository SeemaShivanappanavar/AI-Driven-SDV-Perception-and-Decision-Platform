import json

from kuksa_client.grpc import VSSClient
from dashboard.storage import initialize_database, save_event


KUKSA_HOST = "127.0.0.1"
KUKSA_PORT = 55555

SIGNALS = [
    "Vehicle.Perception.FrameData",
    "Vehicle.Perception.IntegrityStatus",
    "Vehicle.Decision.Status"
]


def main():

    print("\nSDV HISTORY RECORDER")
    print("=" * 45)

    initialize_database()
    print("SQLite database: READY")

    print("Connecting to KUKSA Databroker...")

    recorded_count = 0

    try:
        with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:

            print("KUKSA connection: SUCCESS")
            print("Monitoring three vehicle signals.")
            print("Waiting for updates...\n")

            for updates in client.subscribe_current_values(SIGNALS):

                for path, datapoint in updates.items():

                    if path not in SIGNALS:
                        continue

                    try:
                        value = datapoint.value

                        if isinstance(value, bytes):
                            value = value.decode("utf-8")

                        if isinstance(value, str):
                            data = json.loads(value)
                        elif isinstance(value, dict):
                            data = value
                        else:
                            continue

                        if not isinstance(data, dict):
                            continue

                        save_event(path, data)
                        recorded_count += 1

                        print(
                            f"[RECORDED] {path}\n"
                            f"  Session: {data.get('session_id', 'N/A')}\n"
                            f"  Sequence: {data.get('sequence_number', 'N/A')}\n"
                            f"  Total records: {recorded_count}\n"
                        )

                    except (json.JSONDecodeError, TypeError, ValueError) as error:
                        print(f"[INVALID DATA] {path}: {error}")

    except KeyboardInterrupt:
        print("\nHistory recorder stopped.")

    except Exception as error:
        print(f"\nRecorder error: {error}")

    finally:
        print(f"Total records recorded: {recorded_count}")


if __name__ == "__main__":
    main()
