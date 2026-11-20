import json
import math
from collections import OrderedDict
from datetime import datetime, timezone

from kuksa_client.grpc import VSSClient, Datapoint

KUKSA_HOST = "127.0.0.1"
KUKSA_PORT = 55555

PERCEPTION_SIGNAL = "Vehicle.Perception.FrameData"
INTEGRITY_SIGNAL = "Vehicle.Perception.IntegrityStatus"
DECISION_SIGNAL = "Vehicle.Decision.Status"
DISTANCE_SIGNAL = "Vehicle.Simulation.ObstacleDistance"

MAX_BUFFER_SIZE = 100

pending_messages = OrderedDict()
processed_frames = OrderedDict()

latest_simulated_distance = None
latest_processed_context = None


def get_message_key(data):
    session_id = data.get("session_id")
    sequence_number = data.get("sequence_number")

    if (
        not isinstance(session_id, str)
        or not isinstance(sequence_number, int)
        or isinstance(sequence_number, bool)
    ):
        print("Invalid session ID or sequence number.")
        return None

    return session_id, sequence_number


def store_message(message_type, data):
    """Wait for matching perception and integrity messages."""

    key = get_message_key(data)

    if key is None or key in processed_frames:
        return None

    if key not in pending_messages:
        pending_messages[key] = {}

    pending_messages[key][message_type] = data
    pending_messages.move_to_end(key)

    while len(pending_messages) > MAX_BUFFER_SIZE:
        removed_key, _ = pending_messages.popitem(last=False)
        print("Buffer limit reached. Removed:", removed_key)

    pair = pending_messages[key]

    if "perception" in pair and "integrity" in pair:
        pending_messages.pop(key)
        return pair

    return None


def make_decision(perception, integrity, simulated_distance=None):

    # Integrity always has priority over distance.
    if integrity.get("integrity_status") != "VALID":
        return "CAUTION", "Perception data integrity fault detected"

    detections = perception.get("detections", [])

    valid_detections = [
        detection for detection in detections
        if isinstance(detection, dict)
        and isinstance(detection.get("class"), str)
    ]

    if not valid_detections:
        return "NORMAL", "No object detected; perception data is valid"

    object_names = sorted({
        detection["class"] for detection in valid_detections
    })
    object_description = ", ".join(object_names)

    # Preserve the original decision behaviour until a distance is supplied.
    if simulated_distance is None:
        person_detected = any(
            detection["class"].lower() == "person"
            for detection in valid_detections
        )

        if person_detected:
            return "ALERT", "Person detected; simulated distance unavailable"

        return "NORMAL", "Object detected; simulated distance unavailable"

    if simulated_distance > 20:
        return (
            "NORMAL",
            f"{object_description} detected at {simulated_distance:.1f} m; "
            "distance is above 20 m"
        )

    if simulated_distance > 10:
        return (
            "CAUTION",
            f"{object_description} detected at {simulated_distance:.1f} m; "
            "caution zone"
        )

    if simulated_distance > 5:
        return (
            "WARNING",
            f"{object_description} detected at {simulated_distance:.1f} m; "
            "warning zone"
        )

    return (
        "CRITICAL ALERT",
        f"{object_description} detected at {simulated_distance:.1f} m; "
        "critical distance zone"
    )


def publish_decision(client, perception, integrity, simulated_distance=None):

    decision, reason = make_decision(
        perception,
        integrity,
        simulated_distance
    )

    decision_data = {
        "schema_version": "1.0",
        "session_id": perception["session_id"],
        "sequence_number": perception["sequence_number"],
        "decision": decision,
        "reason": reason,
        "simulated_distance_m": simulated_distance,
        "decision_timestamp": datetime.now(timezone.utc).isoformat()
    }

    client.set_current_values({
        DECISION_SIGNAL: Datapoint(json.dumps(decision_data))
    })

    print("\n" + "=" * 50)
    print("FRAME:", perception["sequence_number"])
    print("SIMULATED DISTANCE:", simulated_distance, "m")
    print("DECISION:", decision)
    print("REASON:", reason)
    print("PUBLISHED TO KUKSA:", DECISION_SIGNAL)
    print("=" * 50)

    return decision


def process_message(client, message_type, data):

    global latest_processed_context

    key = get_message_key(data)

    if key is None:
        return

    # Handle a late integrity update for an already processed frame.
    if key in processed_frames:

        previous = processed_frames[key]

        if message_type == "integrity":

            old_status = previous["integrity"].get("integrity_status")
            new_status = data.get("integrity_status")

            if old_status == "VALID" and new_status != "VALID":

                print("\nLATE INTEGRITY FAULT DETECTED!")
                print("Updating the previous decision to CAUTION.")

                previous["integrity"] = data

                updated_decision = publish_decision(
                    client,
                    previous["perception"],
                    data,
                    latest_simulated_distance
                )

                previous["decision"] = updated_decision

        return

    pair = store_message(message_type, data)

    if pair:

        decision = publish_decision(
            client,
            pair["perception"],
            pair["integrity"],
            latest_simulated_distance
        )

        context = {
            "perception": pair["perception"],
            "integrity": pair["integrity"],
            "decision": decision
        }

        processed_frames[key] = context
        latest_processed_context = context

        processed_frames.move_to_end(key)

        while len(processed_frames) > 1000:
            processed_frames.popitem(last=False)


def process_distance_update(client, value):

    global latest_simulated_distance

    if isinstance(value, bool):
        print("Invalid simulated distance:", value)
        return

    try:
        distance = float(value)
    except (TypeError, ValueError):
        print("Invalid simulated distance:", value)
        return

    if not math.isfinite(distance) or distance < 0:
        print("Invalid simulated distance:", value)
        return

    latest_simulated_distance = distance

    print("\nSIMULATED DISTANCE UPDATED:", distance, "m")

    # Recalculate using the latest processed perception/integrity pair.
    if latest_processed_context is not None:

        context = latest_processed_context

        decision = publish_decision(
            client,
            context["perception"],
            context["integrity"],
            latest_simulated_distance
        )

        context["decision"] = decision


def main():

    print("Starting Fault-Aware Decision Module...")
    print("Connecting to KUKSA Databroker...")

    with VSSClient(KUKSA_HOST, KUKSA_PORT) as client:

        print("Connected successfully!")
        print("Waiting for perception, integrity and distance updates...\n")

        signals = [
            PERCEPTION_SIGNAL,
            INTEGRITY_SIGNAL,
            DISTANCE_SIGNAL
        ]

        for updates in client.subscribe_current_values(signals):

            try:

                if PERCEPTION_SIGNAL in updates:

                    raw = updates[PERCEPTION_SIGNAL].value

                    if raw:
                        perception = json.loads(raw)

                        process_message(
                            client,
                            "perception",
                            perception
                        )

                if INTEGRITY_SIGNAL in updates:

                    raw = updates[INTEGRITY_SIGNAL].value

                    if raw:
                        integrity = json.loads(raw)

                        process_message(
                            client,
                            "integrity",
                            integrity
                        )

                if DISTANCE_SIGNAL in updates:

                    distance = updates[DISTANCE_SIGNAL].value

                    process_distance_update(client, distance)

            except (json.JSONDecodeError, TypeError, KeyError) as error:
                print("Decision processing error:", error)


if __name__ == "__main__":

    try:
        main()

    except KeyboardInterrupt:
        print("\nDecision Module stopped.")
