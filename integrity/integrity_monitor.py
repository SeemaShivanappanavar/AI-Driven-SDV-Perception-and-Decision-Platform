import json
import time
import math

from kuksa_client.grpc import VSSClient, Datapoint


# Configuration
KUKSA_HOST = "127.0.0.1"
KUKSA_PORT = 55555

PERCEPTION_SIGNAL = "Vehicle.Perception.FrameData"
INTEGRITY_SIGNAL = "Vehicle.Perception.IntegrityStatus"

MAX_MESSAGE_AGE_MS = 500
MAX_FUTURE_TIMESTAMP_MS = 1000
SUPPORTED_SCHEMA_VERSION = "1.0"


# Monitoring state
last_sequence = None
last_session = None

statistics = {
    "messages_received": 0,
    "missing_messages": 0,
    "duplicate_messages": 0,
    "out_of_order_messages": 0,
    "stale_messages": 0,
    "invalid_messages": 0
}


def validate_message(data):

    global last_sequence, last_session

    faults = []

    if not isinstance(data, dict):
        return ["Malformed message"]

    required_fields = [
        "schema_version",
        "source_id",
        "session_id",
        "sequence_number",
        "capture_timestamp_ms",
        "detection_count",
        "detections"
    ]

    for field in required_fields:
        if field not in data:
            faults.append(f"Missing field: {field}")

    if faults:
        return faults

    # Validate schema version
    if data["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        faults.append("Unsupported schema version")

    # Validate source ID
    if not isinstance(data["source_id"], str) or not data["source_id"]:
        faults.append("Invalid source ID")

    # Validate session and sequence without immediately
    # modifying monitoring state.
    session = data["session_id"]
    sequence = data["sequence_number"]

    sequence_eligible = False
    sequence_gap_count = 0
    candidate_session = None

    if not isinstance(session, str) or not session:
        faults.append("Invalid session ID")

    elif (
        not isinstance(sequence, int)
        or isinstance(sequence, bool)
        or sequence < 1
    ):
        faults.append("Invalid sequence number")

    else:
        candidate_session = session
        sequence_eligible = True

        previous_sequence = (
            last_sequence if session == last_session else None
        )

        if previous_sequence is not None:

            if sequence == previous_sequence:
                faults.append("Duplicate message")
                sequence_eligible = False

            elif sequence < previous_sequence:
                faults.append("Out-of-order message")
                sequence_eligible = False

            elif sequence > previous_sequence + 1:
                sequence_gap_count = (
                    sequence - previous_sequence - 1
                )

                faults.append(
                    f"Sequence gap: {sequence_gap_count} message(s)"
                )

    # Validate timestamp
    timestamp = data["capture_timestamp_ms"]

    if (
        not isinstance(timestamp, (int, float))
        or isinstance(timestamp, bool)
        or not math.isfinite(timestamp)
    ):
        faults.append("Invalid timestamp")

    else:
        age_ms = time.time() * 1000 - timestamp

        if age_ms > MAX_MESSAGE_AGE_MS:
            faults.append("Stale message")

        if age_ms < -MAX_FUTURE_TIMESTAMP_MS:
            faults.append("Future timestamp")

    # Validate detections
    detections = data["detections"]
    detection_count = data["detection_count"]

    if not isinstance(detections, list):
        faults.append("Invalid detections format")

    elif (
        not isinstance(detection_count, int)
        or isinstance(detection_count, bool)
        or detection_count < 0
    ):
        faults.append("Invalid detection count")

    elif detection_count != len(detections):
        faults.append("Detection count mismatch")

    else:
        for detection in detections:

            if not isinstance(detection, dict):
                faults.append("Invalid detection entry")
                break

            if not all(
                field in detection
                for field in ["class", "confidence", "bbox"]
            ):
                faults.append("Incomplete detection entry")
                break

            confidence = detection["confidence"]
            bbox = detection["bbox"]

            if not isinstance(detection["class"], str):
                faults.append("Invalid object class")
                break

            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not math.isfinite(confidence)
                or not 0 <= confidence <= 1
            ):
                faults.append("Invalid confidence")
                break

            if (
                not isinstance(bbox, list)
                or len(bbox) != 4
                or not all(
                    isinstance(value, (int, float))
                    and not isinstance(value, bool)
                    and math.isfinite(value)
                    for value in bbox
                )
            ):
                faults.append("Invalid bounding box")
                break

    # Commit sequence state only after all other validations pass.
    # A valid sequence gap is accepted and counted once.
    sequence_faults = [
        fault for fault in faults
        if fault.startswith("Sequence gap:")
    ]

    other_faults = [
        fault for fault in faults
        if fault not in sequence_faults
    ]

    if sequence_eligible and not other_faults:
        if candidate_session != last_session:
            last_session = candidate_session
            last_sequence = None

        if last_sequence is None or sequence > last_sequence:
            last_sequence = sequence

        statistics["missing_messages"] += sequence_gap_count

    return faults


def update_statistics(faults):

    for fault in faults:

        if "Duplicate" in fault:
            statistics["duplicate_messages"] += 1

        elif "Out-of-order" in fault:
            statistics["out_of_order_messages"] += 1

        elif "Stale" in fault:
            statistics["stale_messages"] += 1

        elif (
            "Invalid" in fault
            or "Missing" in fault
            or "Malformed" in fault
            or "Incomplete" in fault
            or "mismatch" in fault
            or "Future" in fault
            or "Unsupported" in fault
        ):
            statistics["invalid_messages"] += 1


def publish_integrity_status(client, data, faults):

    status = {
        "schema_version": "1.0",
        "session_id": data.get("session_id", "unknown"),
        "sequence_number": data.get("sequence_number", -1),
        "integrity_status": "FAULT" if faults else "VALID",
        "fault_count": len(faults),
        "faults": faults,
        "statistics": statistics.copy(),
        "monitor_timestamp_ms": int(time.time() * 1000)
    }

    client.set_current_values({
        INTEGRITY_SIGNAL: Datapoint(json.dumps(status))
    })

    print(
        "Integrity Status Published:",
        status["integrity_status"]
    )


def main():

    print("Starting Data Integrity Monitor...")
    print("Connecting to KUKSA...")

    with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:

        print("Connected successfully!")
        print("Monitoring perception messages...\n")

        for updates in client.subscribe_current_values(
            [PERCEPTION_SIGNAL]
        ):

            try:

                raw_message = updates[PERCEPTION_SIGNAL].value

                # Ignore empty initial KUKSA updates
                if raw_message is None:
                    continue

                # Parse incoming JSON
                data = json.loads(raw_message)

                statistics["messages_received"] += 1

                # Validate message
                faults = validate_message(data)

                update_statistics(faults)

                if isinstance(data, dict):
                    print(
                        f"Frame: {data.get('sequence_number', 'Unknown')} | "
                        f"Objects: {data.get('detection_count', 'Unknown')}"
                    )

                if faults:
                    for fault in faults:
                        print("INTEGRITY FAULT:", fault)
                else:
                    print("Integrity Status: VALID")

                # Publish integrity result
                publish_integrity_status(client, data, faults)

                print("Statistics:", statistics)
                print("-" * 50)

            except (json.JSONDecodeError, TypeError, ValueError) as error:

                statistics["invalid_messages"] += 1

                print("Invalid perception message:", error)

                # Malformed JSON cannot provide a matching
                # session ID or sequence number.
                # Publish an unmatchable FAULT for monitoring.
                malformed_data = {}

                publish_integrity_status(
                    client,
                    malformed_data,
                    ["Malformed JSON message"]
                )

            except KeyError as error:

                print("Missing KUKSA update field:", error)


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nIntegrity Monitor stopped.")
        print("Final statistics:", statistics)
